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
    scrape_tool = ScrapeWebsiteTool()
    website_search = WebsiteSearchTool()

    # (application assistant)



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
            "Use 'Search the internet with Serper' to find opportunities with these search queries:\n"
            "- 'creative opportunities today'\n"
            "- 'paid creative jobs Nigeria'\n"
            "- 'creative grants for Nigerians'\n"
            "- 'music, writing, tech, architecture, content creation, fashion, film, visual arts, photography, videography and design jobs'\n\n"
            "Then use 'Read website content' to check these specific sources:\n"
            "- https://opportunitydesk.org\n"
            "- https://opportunitiesforyouth.org\n"
            "- http://africanofilter.org\n"
            "- https://artconnect.com\n"
            "- https://creativepool.com\n"
            "- https://www.artsy.net\n"
            "- https://www.artjobs.com/jobs\n"
            "- https://the-dots.com/jobs/search\n"
            "- https://africanartists.org\n"
            "- https://www.grants.gov\n"
            "- https://careers.unesco.org/go/All-jobs-openings/782502/\n"
            "- https://www.musicinafrica.net\n"
            "- https://trybeafrica.com/search-creative-opportunities/\n\n"
            "Focus on opportunities with:\n"
            "- Deadlines within the next 3 months\n"
            "- Minimum payment of $100 or equivalent in USD, EUR, or NGN\n"
            "- Valid application links"
        ),
        agent=opportunity_agent,
        expected_output="A list of 50 raw opportunity data from these sources",
        tools=[search_tool, scrape_tool, website_search]
    )

    filter_task = Task(
        description=(
            "For each opportunity found, use 'Read website content' to verify:\n"
            "- The application link for the opportunity is working\n"
            "- The deadline hasn't passed\n"
            "- The payment amount meets the minimum requirement\n\n"
            "Use 'Search in a specific website' to verify the opportunity is still active on the source website."
        ),
        agent=opportunity_agent,
        expected_output="A filtered list of relevant opportunities that meet all the criteria given above",
        tools=[scrape_tool, website_search]
    )

    validate_task = Task(
        description=(
            "For each filtered opportunity, use 'Read website content' to collect:\n"
            "1. Basic Info: title, company name\n"
            "2. Details: event description, job description, deliverables\n"
            "3. Requirements: location, deadline\n"
            "4. Payment: amount and currency\n"
            "5. Application: working direct link to apply for the opportunity\n\n"
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
            "    'link': 'Direct link to the application page to apply for the opportunity'\n"
            "}"
        ),
        agent=opportunity_agent,
        expected_output="A validated list of 10 formatted opportunities in JSON structure",
        output_json=OpportunityList,
        tools=[scrape_tool, website_search]
    )
    

    # Put it all together
    crew = Crew(
        agents=[opportunity_agent],
        tasks=[search_task, filter_task, validate_task],
        verbose=True,
    )

    result = crew.kickoff()
    return result

        # source crew-env/bin/activate

if __name__ == "__main__":
    opportunities = find_creative_opportunities()
    # print(opportunities)
    print(opportunities["opportunities"])

    # result = split_json_string(opportunities)
    # print(result)
