# Warning control
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Task, Crew, LLM
from crewai_tools.tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
from pydantic import BaseModel, Json
from typing import List, Any

from dotenv import load_dotenv
import os

class Payment(BaseModel):
    currency: str
    total: int

class Opportunity(BaseModel):
    title: str
    company: str
    companyEmail: str
    event: str
    eventDescription: str
    description: str
    jobLocation: str
    payment: Payment
    deadline: str
    tags: List[str]
    deliverables: List[str]
    link: str


class OpportunityList(BaseModel):
    opportunities: List[Opportunity]

def is_valid_link(url: str) -> bool:
    try:
        response = requests.head(url, timeout=10)
        return response.status_code < 400
    except Exception:
        return False


def find_creative_opportunities():
    load_dotenv()
    api_key = os.getenv("SERPER_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7,
    )

    # Create a search tool
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool(timeout=30)  
    website_search = WebsiteSearchTool()

    # Define your agent
    opportunity_agent = Agent(
        name="Global Opportunity Agent",
        llm=llm,
        role="Creative Opportunity Researcher",
        goal=(
            "Search for high-quality opportunities"
            "This includes jobs, grants, competitions, partnerships, exhibitions, festivals and open calls across industries like music, writing, tech, architecture, content creation, fashion, film, visual arts, photography, videography and design."
            "Ensure these opportunities are currently open and paid"
            "Avoid blog aggregators or listicles. Focus on official sources and links."
        ),
        backstory=(
            "You are an expert global opportunity researcher. "
            "You specialize in finding international and local opportunities. "
            "You know how to identify credible, valuable, and active listings by exploring various trusted online sources. "
            "You present this information in a clean, structured format with all the details needed."
        ),
        tools=[search_tool, scrape_tool],
        verbose=True,
        allow_delegation=False,
    )
    

    # Define tasks
    search_task = Task(
        description=(
            "Use 'Search the internet with Serper' to find up to 30 high-quality opportunities that match these queries:\n"
            "- 'creative opportunities today'\n"
            "- 'creative grants for Nigerians'\n"
            "- 'music industry jobs Nigeria'\n"
            "- 'writing opportunities Africa'\n"
            "- 'tech jobs creative sector'\n"
            "- 'architecture competitions Africa'\n"
            "- 'content creator jobs remote'\n"
            "- 'fashion design opportunities Nigeria'\n"
            "- 'film production jobs Africa'\n"
            "- 'visual arts grants Nigeria'\n"
            "- 'photography jobs creative'\n"
            "- 'videography opportunities remote'\n"
            "- 'design jobs Africa'\n\n"
            "Provide exactly 20 relevant opportunities"
        ),
        agent=opportunity_agent,
        expected_output="A list of 30 raw opportunity data from these sources",
        tools=[search_tool]
    )

    filter_task = Task(
        description=(
            "For each opportunity found, use the 'Read website content' tool to verify:\n"
            "- The application link for the opportunity does not go to a 404 page.\n"
            "- Keep only those with valid links (no 404s, using 'website_search' and 'scrape_tool').\n"
            "- Ensure they opportunity's deadline date isnt before today date (deadline within 3 months from today).\n"
            "- Do not return opportunities that are past deadline date.\n"
            "- The application link for the opportunity is a valid link from the website the opportunity was found.\n"
            "Focus only on the official opportunity page, ignoring external articles or blog posts."
        ),
        agent=opportunity_agent,
        expected_output="A filtered list of 20 relevant opportunities that meet all the criteria given in the description",
        tools=[scrape_tool, website_search]
    )

    validate_task = Task(
        description=(
            "From the 20 detailed opportunities collect:\n"
            "1. Basic Info: title, company name\n"
            "2. Details: event description, job description, deliverables\n"
            "3. Requirements: location, deadline\n"
            "4. Payment: amount and currency\n"
            "5. Application: a direct link to apply for the opportunity\n\n"
            "- Keep 10 final validated opportunities.\n\n"
            "Format the data into this structure:\n"
            "{\n"
            "    'title': 'Opportunity title',\n"
            "    'company': 'Organization or company name',\n"
            "    'companyEmail': 'Official email contact (must be valid)',\n"
            "    'event': 'Same as title or specific event name',\n"
            "    'eventDescription': 'Detailed description of the job, event, grant, or competition',\n"
            "    'description': 'Summary of what the creative is expected to do or submit',\n"
            "    'jobLocation': 'Remote, Onsite (city), or Hybrid',\n"
            "    'payment': {\n"
            "        'currency': 'USD, EUR, or NGN',\n"
            "        'total': Payment for the opportunity \n"
            "    },\n"
            "    'deadline': 'Deadline or end date in ISO format',\n"
            "    'tags': ['Relevant tags like Writers, Fashion, Filmmakers'],\n"
            "    'deliverables': ['A bullet point or sentence describing the expected submission or participation'],\n"
            "    'link': 'Direct link to apply for the opportunity'\n"
            "}"
        ),
        agent=opportunity_agent,
        expected_output="A validated list of 10 formatted opportunities in JSON structure",
        output_json=OpportunityList,
    )
    

    # Put it all together
    crew = Crew(
        agents=[opportunity_agent],
        tasks=[search_task, filter_task, validate_task],
        verbose=True,
    )


    result = crew.kickoff()
    validated_opportunities = result["opportunities"]

    # Validate links
    for opp in validated_opportunities:
        if not is_valid_link(opp["link"]):
            print(f"Warning: Invalid link detected for {opp['title']} - {opp['link']}")
            opp["link_verified"] = False
        else:
            opp["link_verified"] = True

    return {"opportunities": validated_opportunities}

if __name__ == "__main__":
    opportunities = find_creative_opportunities()
    print(opportunities["opportunities"])

