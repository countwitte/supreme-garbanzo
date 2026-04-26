import asyncio
from typing import Optional, List, Dict, Any
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig


class ChessScotlandScraper:
    def __init__(self):
        self.base_url = "https://www.chessscotland.com"

    async def get_player_data(self, name: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/membership/members/"
        
        extraction_strategy = JsonCssExtractionStrategy(
            {
                "baseSelector": "tr:has(td)",
                "name": f"td:contains({name})",
                "pnum": "td:nth-child(1)",
                "name_extracted": "td:nth-child(2)",
                "standard_grade": "td:nth-child(3)",
                "allegro_grade": "td:nth-child(4)",
                "club": "td:nth-child(5)",
            },
            source_type="html",
        )

        config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            css_selector="table.member-list tbody tr",
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if result.success and result.extracted_content:
                return self._parse_player_result(result.extracted_content, name)
        return None

    def _parse_player_result(self, content: str, name: str) -> Optional[Dict[str, Any]]:
        lines = content.strip().split("\n")
        for line in lines:
            if name.lower() in line.lower():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    return {
                        "pnum": parts[0] if parts[0] else "",
                        "name": parts[1] if parts[1] else name,
                        "standard_grade": self._parse_grade(parts[2]),
                        "allegro_grade": self._parse_grade(parts[3]),
                        "club": parts[4] if len(parts) > 4 else "",
                    }
        return None

    def _parse_grade(self, value: str) -> Optional[int]:
        try:
            return int(value) if value and value != "-" else None
        except (ValueError, TypeError):
            return None

    async def get_league_results(
        self, league_query: str
    ) -> Optional[List[Dict[str, Any]]]:
        url = f"{self.base_url}/grading/results/2026/"

        extraction_strategy = JsonCssExtractionStrategy(
            {
                "league_name": "a",
                "league_link": "a::attr(href)",
            },
            source_type="html",
        )

        config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            css_selector="table.league-list, table.results",
            fit_markdown=True,
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if not result.success or not result.extracted_content:
                return None

            league_link = self._find_league_link(result.extracted_content, league_query)
            if not league_link:
                return None

            return await self._scrape_league_table(f"{self.base_url}{league_link}")

        return None

    def _find_league_link(self, content: str, query: str) -> Optional[str]:
        lines = content.strip().split("\n")
        for line in lines:
            if query.lower() in line.lower() and "href=" in line:
                start = line.find("href=") + 6
                end = line.find(")", start)
                if end > start:
                    return line[start:end]
        return None

    async def _scrape_league_table(
        self, url: str
    ) -> Optional[List[Dict[str, Any]]]:
        extraction_strategy = JsonCssExtractionStrategy(
            {
                "rank": "td:nth-child(1)",
                "team_name": "td:nth-child(2)",
                "played": "td:nth-child(3)",
                "points": "td:nth-child(4)",
            },
            source_type="html",
        )

        config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            css_selector="table.standings tbody tr",
            fit_markdown=True,
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if result.success and result.extracted_content:
                return self._parse_league_table(result.extracted_content)
        return None

    def _parse_league_table(
        self, content: str
    ) -> List[Dict[str, Any]]:
        standings = []
        lines = content.strip().split("\n")
        
        for line in lines:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4 and parts[0].isdigit():
                    standings.append({
                        "rank": int(parts[0]),
                        "team_name": parts[1],
                        "played": int(parts[2]) if parts[2].isdigit() else 0,
                        "points": float(parts[3]) if parts[3].replace(".", "").isdigit() else 0.0,
                    })
        
        return standings


async def main():
    scraper = ChessScotlandScraper()
    
    result = await scraper.get_player_data("John Smith")
    print("Player data:", result)


if __name__ == "__main__":
    asyncio.run(main())