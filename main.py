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
    image: str
    jobLocation: str
    payment: Payment
    startDate: str
    endDate: str
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



    # Define your agent
    opportunity_agent = Agent(
        name="Global Opportunity Agent",
        llm=llm,
        role="Creative Opportunity Researcher",
        goal=(
            "Search for high-quality opportunities for Nigerian creatives. "
            "This includes jobs, grants, competitions, partnerships, and open calls across creative industries like music, writing, tech, architecture, content creation,  fashion, film, visual arts, photography, and design."
            "Ensure these opportunities are currently open, paid and specify if they are remote, onsite (city), or hybrid."
            "Avoid blog aggregators or listicles. Focus on official sources and links."
        ),
        backstory=(
            "You are an expert global opportunity researcher for the creative economy. "
            "You specialize in finding international and local opportunities tailored to Nigerian creatives across all disciplines. "
            "You know how to identify credible, valuable, and active listings by exploring various trusted online sources. "
            "You present this information in a clean, structured format with all the necessary details."
        ),
        tools=[search_tool, scrape_tool],
        verbose=True,
        allow_delegation=False,
    )

    # Define a task
    find_opportunities = Task(
        description=(
            "Search globally across multiple trusted sources for real-time opportunities "
            "relevant to Nigerian creatives in 2025. Focus on opportunities with deadlines within the next 3 months. "
            "These should include jobs, grants, competitions, or partnerships "
            "in music, writing, tech, architecture, content creation, fashion, film, visual arts, photography, and design. "
            "Prioritize opportunities with minimum payment of $500 or equivalent in USD, EUR, or NGN.\n\n"
            "Focus on official sources including but not limited to:\n"
            "- Behance Jobs\n"
            "- Dribbble Jobs\n"
            "- Creative Pool\n"
            "- Artsy\n"
            "- ArtJobs\n"
            "- Creative Opportunities (UK)\n"
            "- African Artists' Foundation\n"
            "- British Council Nigeria\n"
            "- grants.gov\n"
            "- UNESCO jobs\n"
            "- Music in Africa\n"
            "- artconnect.com\n"
            "- opportunitydesk.org\n"
            "- trybeafrica.com\n"
            "- opportunitiesforyouth.org\n"
            "- africanofilter.org\n\n"
            "Prioritize these types of opportunities:\n"
            "- Paid residencies\n"
            "- Artist grants\n"
            "- Creative fellowships\n"
            "- International exhibitions\n"
            "- Film festivals\n"
            "- Music competitions\n"
            "- Design challenges\n\n"
            "For each opportunity, verify and include:\n"
            "- Title of the opportunity or job\n"
            "- Company name\n"
            "- Company email (must be a valid, working email)\n"
            "- Event description\n"
            "- Description of the opportunity or job\n"
            "- Deliverables expected from the creative\n"
            "- Valid Link to apply for the opportunity (must be a direct link to the application page)\n"
            "- Amount in number and currency for the opportunity\n"
            "- Location (remote, onsite with specific city, or hybrid)\n"
            "- Start and end dates for the application\n"
            "Validation Requirements:\n"
            "- Verify the application process is still open\n"
            "- Confirm the contact information is valid\n"
            "- Check that application requirements are clearly listed\n"
            "- Do not include any link that redirects to a 404\n"
            "- Each opportunity must include a working direct link to the live opportunity application page\n"
            "- Do not pick opportunities where the amount isn't specified\n"
            "- Verify the opportunity is still accepting applications by checking the application page"
        ),
        expected_output="""
            Return in a list 10 opportunities formatted as JSON objects with the following structure:
            {
                "title": "Opportunity title",
                "company": "Organization or company name (if available)",
                "companyEmail": "Official email contact (must be valid)",
                "event": "Same as title or specific event name",
                "eventDescription": "Detailed description of the job, event, grant, or competition",
                "description": "Summary of what the creative is expected to do or submit",
                "jobLocation": "Remote, Onsite (city), or Hybrid",
                "payment": {
                    "currency": "USD, EUR, or NGN",
                    "total": amount 
                },
                "startDate": "Start date in ISO format",
                "endDate": "Deadline or end date in ISO format",
                "tags": ["Relevant tags like 'Writers', 'Fashion', 'Filmmakers'"],
                "deliverables": ["A bullet point or sentence describing the expected submission or participation"],
                "link": "Direct link to the source page of the opportunity",
            }
            Ensure each JSON object in the list is fully filled with accurate information and all links are working.
            """,
        agent=opportunity_agent,
        output_json=OpportunityList
    )

    # Put it all together
    crew = Crew(
        agents=[opportunity_agent],
        tasks=[find_opportunities],
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
