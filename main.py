# Warning control
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Task, Crew, LLM
from crewai_tools.tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
from pydantic import BaseModel
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
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    llm = LLM(
        model="claude-3-opus-20240229",
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
            "This includes fellowships, Company funding, startup funding, music funding, Art funding, grants, competitions, partnerships, exhibitions, festivals and open calls across industries like music, writing, architecture, content creation, fashion, film, visual arts and photography."
            "Ensure these opportunities are currently open and paid"
            "Avoid blog aggregators or listicles. Focus on official sources and links."
        ),
        backstory=(
            "You are an expert global opportunity researcher. "
            "You specialize in finding opportunities for creatives in Nigeria. "
            "You know how to identify credible, valuable, and active listings by exploring various trusted online sources. "
            "You present this information in a clean, structured format with all the details needed."
        ),
        tools=[search_tool, scrape_tool],
        verbose=True,
        max_iterations=3,
        allow_delegation=False,
    )
    

    # Define tasks
    search_task = Task(
        description=(
            "Use 'Search the internet with Serper' to find up to high-quality opportunities that match these queries:\n"
            "- 'Music funding opportunities today'\n"
            "- 'Startup funding and grants opportunities'\n"
            "- 'Music grants for Nigerians'\n"
            "- 'funding for Arts development in Nigeria'\n"
            "- 'Music industry jobs Nigeria'\n"
            "- 'Festivals and Fellowships in Nigeria'\n"
            "- 'Music production jobs Africa'\n"
            "- 'Writing opportunities in Africa'\n"
            "- 'Content creator jobs remote'\n"
            "- 'Film production jobs Africa'\n"
            "Once you have gotten the first 30 relevant opportunities move to the next task'\n"
        ),
        agent=opportunity_agent,
        expected_output="A list of opportunities from these sources",
        tools=[search_tool]
    )

    filter_task = Task(
        description=(
            "For each opportunity found verify:\n"
            "- The application link for the opportunity does not go to a 404 page.\n"
            "- Keep only those with valid links (no 404s, using 'website_search' and 'scrape_tool').\n"
            "- Ensure they opportunity's deadline date isnt before today date (deadline within 3 months from today).\n"
            "- Do not return opportunities that are past deadline date.\n"
            "- The application link for the opportunity is a valid link from the website the opportunity was found.\n"
            "- The opportunity is not a blog aggregator or listicle.\n"
            "- The payment is from $1000 and it's equaivalent and above in Naira\n"
            "Focus only on the official opportunity page, ignoring external articles or blog posts."
        ),
        agent=opportunity_agent,
        expected_output="A filtered list of 20 relevant opportunities that meet all the criteria given in the description",
    )

    validate_task = Task(
        description=(
            "From the 20 detailed opportunities collect:\n"
            "1. Basic Info: title, company name\n"
            "2. Details: event description, job description, deliverables\n"
            "3. Requirements: location, deadline\n"
            "4. Payment: amount and currency\n"
            "5. Application: a direct link to apply for the opportunity\n\n"
            "Format the data into this structure:\n"
            "{\n"
            "    'title': 'title of the opportunity',\n"
            "    'company': 'Organization or company name',\n"
            "    'companyEmail': 'Official email contact (must be valid)',\n"
            "    'event': 'The name of the event on the site',\n"
            "    'eventDescription': 'Detailed description of the opportunity found on the site',\n"
            "    'description': 'Summary of what the creative is expected to do or submit',\n"
            "    'jobLocation': 'Remote, Onsite (city), or Hybrid',\n"
            "    'payment': {\n"
            "        'currency': 'the currency of the payment for the opportunity',\n"
            "        'total': Payment for the opportunity(amount its worth) \n"
            "    },\n"
            "    'deadline': 'Deadline or end date of the opportunity',\n"
            "    'tags': ['Relevant tags for the opportunity like Writers, Fashion, Filmmakers'],\n"
            "    'deliverables': ['A bullet point or sentence describing the expected submission or participation for the opportunity'],\n"
            "    'link': 'Direct link to apply for the opportunity found on the site'\n"
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

