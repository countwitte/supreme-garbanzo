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
            
            await page.goto(f"{self.base_url}/grading/search-players")
            await page.fill('input[name="surname"]', name)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            
            if "No players found" in content:
                await browser.close()
                return None
            
            # Try to find link using Playwright selector
            link = await page.query_selector(f'a:has-text("{name.split()[0]}")')
            if not link:
                await browser.close()
                return None
            
            player_link = await link.get_attribute('href')
            player_name = await link.inner_text()
            
            pnum_match = re.search(r'/player/(\d+)', player_link)
            pnum = pnum_match.group(1) if pnum_match else ""
            
            await page.goto(f"{self.base_url}{player_link}")
            await page.wait_for_load_state('networkidle')
            player_html = await page.content()
            
            grade = self._extract_grade(player_html, "Standard")
            allegro = self._extract_grade(player_html, "Allegro")
            club = self._extract_club(player_html)
            
            await browser.close()
            return {
                "name": player_name,
                "pnum": pnum,
                "standard_grade": grade,
                "allegro_grade": allegro,
                "club": club,
            }

    def _extract_grade(self, html: str, grade_type: str) -> Optional[int]:
        # The first game's "Used" column has the current grade
        match = re.search(r'Grade Type:.*?</td><td>([^<]+)</td>', html)
        if match:
            # Actually need to parse the table - get first data row's Used column
            pass
        # Find in table - look for header "Used" and get corresponding cell
        headers = re.findall(r'<th>([^<]+)</th>', html)
        used_idx = None
        for i, h in enumerate(headers):
            if 'Used' in h:
                used_idx = i
                break
        if used_idx is not None:
            # Get first data row
            data_match = re.search(r'<tr[^>]*>.*?</tr>', html)
            if data_match:
                row_html = data_match.group()
                cells = re.findall(r'<td[^>]*>([^<]+)</td>', row_html)
                if len(cells) > used_idx:
                    try:
                        return int(cells[used_idx])
                    except (ValueError, IndexError):
                        pass
        # Fallback - just get any 4-digit grade from page
        match = re.search(r'<td>(\d{4})</td>', html)
        if match:
            return int(match.group(1))
        return None

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