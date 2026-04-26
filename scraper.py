import asyncio
import re
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright


class ChessScotlandScraper:
    def __init__(self):
        self.base_url = "https://www.chessscotland.com"

    async def get_player_data(self, name: str) -> Optional[Dict[str, Any]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Try to split into forename and surname
            name_parts = name.split()
            surname = name_parts[-1]  # Assume last part is surname
            forename = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''
            
            await page.goto(f"{self.base_url}/grading/search-players")
            # Search by surname first
            await page.fill('input[name="surname"]', surname)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            
            if "No players found" in content:
                await browser.close()
                return None
            
            # Try to find link using Playwright selector - gets first match
            # Improve by looking for full name if provided
            name_parts = name.split()
            if len(name_parts) >= 2:
                # Try full name
                link = await page.query_selector(f'a:has-text("{name}")')
            if not link:
                # Fall back to first match with surname
                link = await page.query_selector(f'a:has-text("{name_parts[0]}")')
            if not link:
                await browser.close()
                return None
            
            player_link = await link.get_attribute('href')
            player_name = await link.inner_text()
            
            pnum_match = re.search(r'/player/(\d+)', player_link)
            pnum = pnum_match.group(1) if pnum_match else ""
            
            # Get standard grade
            await page.goto(f"{self.base_url}/grading/player/{pnum}/2026/Standard")
            await page.wait_for_load_state('networkidle')
            # Get grade from page text - look for 4-digit numbers in main content
            standard_text = await page.inner_text('main')
            grade = self._extract_grade(standard_text, "Standard")
            
            # Get allegro grade
            await page.goto(f"{self.base_url}/grading/player/{pnum}/2026/Allegro")
            await page.wait_for_load_state('networkidle')
            allegro_text = await page.inner_text('main')
            allegro = self._extract_grade(allegro_text, "Allegro")
            
            # Get club from standard page text
            club = self._extract_club(standard_text)
            
            await browser.close()
            return {
                "name": player_name,
                "pnum": pnum,
                "standard_grade": grade.get("published"),
                "standard_grade_live": grade.get("live"),
                "allegro_grade": allegro.get("published"),
                "allegro_grade_live": allegro.get("live"),
                "club": club,
            }

    def _extract_grade(self, text: str, grade_type: str) -> dict:
        import re
        lines = text.split('\n')
        
        published = None
        live = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Published is 2 lines after "Published" label
            if stripped == 'Published' and i + 2 < len(lines):
                try:
                    val = int(lines[i + 2].strip())
                    if 100 <= val <= 2500:
                        published = val
                except:
                    pass
            # Live is 2 lines after "Live" label
            if stripped == 'Live' and i + 2 < len(lines):
                try:
                    val = int(lines[i + 2].strip())
                    if 100 <= val <= 2500:
                        live = val
                except:
                    pass
        
        return {"published": published, "live": live}

    def _extract_club(self, html: str) -> str:
        match = re.search(r'Club[^:]*:\s*<td[^>]*>([^<]+)<', html)
        if match:
            return match.group(1).strip()
        return ""

    async def get_league_results(
        self, league_query: str
    ) -> Optional[List[Dict[str, Any]]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto(f"{self.base_url}/grading/results/2026/")
            await page.wait_for_load_state('networkidle')
            
            content = await page.content()
            
            league_link = self._find_league_link(content, league_query)
            if not league_link:
                await browser.close()
                return None
            
            await page.goto(f"{self.base_url}{league_link}")
            await page.wait_for_load_state('networkidle')
            table_html = await page.content()
            
            standings = self._parse_league_table(table_html)
            await browser.close()
            return standings

    def _find_league_link(self, content: str, query: str) -> Optional[str]:
        links = re.findall(r'<a href="(/grading/results/[^"]+)">([^<]+)</a>', content)
        for link, name in links:
            if query.lower() in name.lower():
                return link
        return None

    def _parse_league_table(self, content: str) -> List[Dict[str, Any]]:
        standings = []
        rows = re.findall(r'<tr[^>]*>.*?</tr>', content)
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>([^<]+)</t[dh]>', row)
            if len(cells) >= 4 and cells[0].isdigit():
                standings.append({
                    "rank": int(cells[0]),
                    "team_name": cells[1],
                    "played": int(cells[2]) if cells[2].isdigit() else 0,
                    "points": float(cells[3]) if cells[3].replace(".", "").isdigit() else 0.0,
                })
        return standings


async def main():
    scraper = ChessScotlandScraper()
    
    result = await scraper.get_player_data("Comerford")
    print("Player data:", result)


if __name__ == "__main__":
    asyncio.run(main())