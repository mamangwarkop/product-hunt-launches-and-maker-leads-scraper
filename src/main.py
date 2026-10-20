"""Product Hunt Launches & Maker Leads Enricher Actor.

Extracts daily Product Hunt launches, resolves external startup websites,
crawls for founder emails, socials, and marketing tracking pixels,
and generates personalized outreach pitch hooks for sales agencies and B2B growth hackers.
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import aiohttp
from apify import Actor

FEED_URL = "https://www.producthunt.com/feed"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,5}")
INVALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico", ".css", ".js"}

COMMON_IGNORED_EMAILS = {
    "sentry@io", "wixpress@com", "example@example.com", "domain@example.com",
    "user@domain.com", "support@github.com"
}


async def resolve_website_and_enrich(
    session: aiohttp.ClientSession,
    redirect_url: str,
    product_title: str,
    tagline: str,
    sem: asyncio.Semaphore,
) -> dict:
    """Follows Product Hunt redirect to the startup website and enriches contact & pixel data."""
    async with sem:
        website_url = None
        emails: list[str] = []
        phones: list[str] = []
        socials: dict[str, str] = {}
        installed_pixels: list[str] = []
        missing_pixels: list[str] = []

        try:
            # 1. Resolve startup destination website via Location header (avoids bot trapping)
            target_url = None
            async with session.get(redirect_url, timeout=10, allow_redirects=False) as resp1:
                loc = resp1.headers.get("Location")
                if loc and loc.startswith("http"):
                    target_url = loc
                elif resp1.status == 200:
                    target_url = str(resp1.url)

            if not target_url or "producthunt.com" in target_url:
                # Fallback to direct resolution
                async with session.get(redirect_url, timeout=12, allow_redirects=True) as resp2:
                    if "producthunt.com" not in str(resp2.url):
                        target_url = str(resp2.url)

            if not target_url or "producthunt.com" in target_url:
                return {
                    "websiteUrl": None,
                    "emails": [],
                    "phoneNumbers": [],
                    "socials": {},
                    "installedPixels": [],
                    "missingPixels": ["Meta Pixel", "Google Analytics/GTM", "TikTok Pixel"],
                    "startupLeadScore": 25,
                    "agencyPitchAngle": f"Saw {product_title} launched on Product Hunt ('{tagline}'). Perfect timing for an introductory partnership pitch.",
                }

            parsed = urlparse(target_url)
            website_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

            # 2. Crawl startup destination website
            async with session.get(target_url, timeout=12, allow_redirects=True) as resp:
                html = await resp.text(errors="replace")
                
                # 2. Extract Emails
                raw_emails = EMAIL_REGEX.findall(html)
                for em in raw_emails:
                    em_lower = em.lower().strip(".")
                    if any(em_lower.endswith(ext) for ext in INVALID_EXTENSIONS):
                        continue
                    if em_lower in COMMON_IGNORED_EMAILS:
                        continue
                    if len(em_lower) < 5 or len(em_lower) > 60:
                        continue
                    if em_lower not in emails:
                        emails.append(em_lower)

                # 3. Extract Phones / WhatsApp
                raw_phones = PHONE_REGEX.findall(html)
                for ph in raw_phones:
                    cleaned_ph = re.sub(r"[^\d+]", "", ph)
                    if 8 <= len(cleaned_ph) <= 15 and cleaned_ph not in phones:
                        phones.append(cleaned_ph)
                        if len(phones) >= 3:
                            break

                # 4. Extract Socials
                tw = re.findall(r'https?://(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{3,25})', html)
                if tw:
                    socials["twitter"] = f"https://x.com/{tw[0]}"

                gh = re.findall(r'https?://github\.com/([a-zA-Z0-9_-]{2,35})', html)
                if gh and gh[0].lower() not in {"topics", "site", "about"}:
                    socials["github"] = f"https://github.com/{gh[0]}"

                disc = re.findall(r'https?://discord\.(?:gg|com/invite)/([a-zA-Z0-9_-]+)', html)
                if disc:
                    socials["discord"] = f"https://discord.gg/{disc[0]}"

                li = re.findall(r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)', html)
                if li:
                    socials["linkedin"] = f"https://www.linkedin.com/company/{li[0]}"

                # 5. Check Installed & Missing Pixels
                html_lower = html.lower()
                if "connect.facebook.net" in html_lower or "fbq(" in html_lower:
                    installed_pixels.append("Meta Pixel")
                else:
                    missing_pixels.append("Meta Pixel")

                if (
                    "googletagmanager.com" in html_lower
                    or "google-analytics.com" in html_lower
                    or "gtag(" in html_lower
                ):
                    installed_pixels.append("Google Analytics/GTM")
                else:
                    missing_pixels.append("Google Analytics/GTM")

                if "analytics.tiktok.com" in html_lower or "ttq." in html_lower:
                    installed_pixels.append("TikTok Pixel")
                else:
                    missing_pixels.append("TikTok Pixel")

        except Exception as e:
            Actor.log.warning(f"Could not enrich website for {product_title}: {e}")

        # Compute startup lead score (0-100)
        score = 30
        if emails:
            score += 25
        if socials:
            score += 15
        if "Google Analytics/GTM" in installed_pixels:
            score += 15
        if missing_pixels:
            score += 15  # Indicates clear growth opportunity to pitch!

        score = min(score, 100)

        # Generate personalized pitch angle
        if "Meta Pixel" in missing_pixels and "Google Analytics/GTM" in installed_pixels:
            pitch = (
                f"Saw {product_title} launched on Product Hunt ('{tagline}'). "
                f"You're tracking traffic with Google Analytics, but missing Meta Pixel retargeting—"
                f"retargeting your launch day visitors could easily double day-1 activation."
            )
        elif "Meta Pixel" in installed_pixels and "TikTok Pixel" in missing_pixels:
            pitch = (
                f"Congrats on the {product_title} launch! Noticed active Meta retargeting, "
                f"but no TikTok pixel active yet for short-form viral product demos."
            )
        elif emails:
            pitch = (
                f"Loved the launch of {product_title} on Product Hunt. Reaching out directly "
                f"to support your post-launch distribution and customer onboarding."
            )
        else:
            pitch = (
                f"Saw {product_title} on today's Product Hunt leaderboards ('{tagline}'). "
                f"Great positioning for B2B expansion."
            )

        return {
            "websiteUrl": website_url,
            "emails": emails[:5],
            "phoneNumbers": phones[:3],
            "socials": socials,
            "installedPixels": installed_pixels,
            "missingPixels": missing_pixels,
            "startupLeadScore": score,
            "agencyPitchAngle": pitch,
        }


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        max_items = int(actor_input.get("maxItems", 50))
        enrich_websites = bool(actor_input.get("enrichWebsites", True))
        filter_keywords = [
            k.strip().lower() for k in actor_input.get("filterKeywords", []) if k.strip()
        ]

        Actor.log.info(
            f"Starting Product Hunt Launches Scraper | maxItems={max_items} | "
            f"enrichWebsites={enrich_websites} | filters={filter_keywords}"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1. Fetch Product Hunt Atom Feed
            try:
                async with session.get(FEED_URL, timeout=15) as resp:
                    if resp.status != 200:
                        Actor.log.error(f"Failed to fetch feed: HTTP {resp.status}")
                        return
                    feed_xml = await resp.text(errors="replace")
            except Exception as e:
                Actor.log.error(f"Feed request error: {e}")
                return

            try:
                root = ET.fromstring(feed_xml)
            except Exception as e:
                Actor.log.error(f"XML parse error: {e}")
                return

            entries = root.findall("atom:entry", ATOM_NS)
            Actor.log.info(f"Total entries discovered in feed: {len(entries)}")

            parsed_launches = []
            for entry in entries:
                title_elem = entry.find("atom:title", ATOM_NS)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled"

                # Published date
                pub_elem = entry.find("atom:published", ATOM_NS)
                published_at = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else None

                # PH Link
                link_elem = entry.find("atom:link", ATOM_NS)
                ph_url = link_elem.attrib.get("href", "") if link_elem is not None else ""

                # Maker name
                maker_name = None
                author_elem = entry.find("atom:author", ATOM_NS)
                if author_elem is not None:
                    name_elem = author_elem.find("atom:name", ATOM_NS)
                    if name_elem is not None and name_elem.text:
                        maker_name = name_elem.text.strip()

                # Tagline and redirect link from content HTML
                content_elem = entry.find("atom:content", ATOM_NS)
                content_html = content_elem.text if content_elem is not None and content_elem.text else ""

                tagline = ""
                redirect_link = ""

                # Extract first <p> text as tagline
                tagline_match = re.search(r"<p>\s*([^<]+?)\s*</p>", content_html)
                if tagline_match:
                    tagline = tagline_match.group(1).strip()

                # Extract direct redirect link (supports both http and https)
                redirect_match = re.search(r'href="(https?://(?:www\.)?producthunt\.com/r/p/[^"]+)"', content_html)
                if redirect_match:
                    redirect_link = redirect_match.group(1)

                # Filter by keywords if provided
                if filter_keywords:
                    searchable_text = f"{title} {tagline}".lower()
                    if not any(fk in searchable_text for fk in filter_keywords):
                        continue

                parsed_launches.append({
                    "productTitle": title,
                    "tagline": tagline,
                    "makerName": maker_name,
                    "productHuntUrl": ph_url,
                    "publishedAt": published_at,
                    "redirectLink": redirect_link,
                })

                if len(parsed_launches) >= max_items:
                    break

            Actor.log.info(f"Enriching {len(parsed_launches)} launches...")

            # 2. Enrich website data concurrently
            sem = asyncio.Semaphore(10)

            async def process_one(launch: dict):
                enrich_data = {
                    "websiteUrl": None,
                    "emails": [],
                    "phoneNumbers": [],
                    "socials": {},
                    "installedPixels": [],
                    "missingPixels": [],
                    "startupLeadScore": 30,
                    "agencyPitchAngle": f"Saw {launch['productTitle']} launched on Product Hunt ('{launch['tagline']}').",
                }

                if enrich_websites and launch.get("redirectLink"):
                    enrich_data = await resolve_website_and_enrich(
                        session=session,
                        redirect_url=launch["redirectLink"],
                        product_title=launch["productTitle"],
                        tagline=launch["tagline"],
                        sem=sem,
                    )

                result = {
                    "productTitle": launch["productTitle"],
                    "tagline": launch["tagline"] or None,
                    "makerName": launch["makerName"] or None,
                    "productHuntUrl": launch["productHuntUrl"],
                    "publishedAt": launch["publishedAt"] or None,
                    "websiteUrl": enrich_data.get("websiteUrl"),
                    "emails": enrich_data.get("emails", []),
                    "phoneNumbers": enrich_data.get("phoneNumbers", []),
                    "socials": enrich_data.get("socials", {}),
                    "installedPixels": enrich_data.get("installedPixels", []),
                    "missingPixels": enrich_data.get("missingPixels", []),
                    "startupLeadScore": enrich_data.get("startupLeadScore", 30),
                    "agencyPitchAngle": enrich_data.get("agencyPitchAngle"),
                }
                await Actor.push_data(result)
                Actor.log.info(
                    f"[+] Pushed {launch['productTitle']} | Score: {result['startupLeadScore']} | "
                    f"Emails: {len(result['emails'])}"
                )

            tasks = [process_one(l) for l in parsed_launches]
            await asyncio.gather(*tasks)

        Actor.log.info("Finished scraping and enriching Product Hunt launches successfully.")


if __name__ == "__main__":
    asyncio.run(main())
