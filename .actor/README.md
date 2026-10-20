# Product Hunt Launches & Maker Leads Enricher (Emails, Socials & Pixels)

> **The fastest, most actionable Product Hunt lead extraction actor.** Scrapes daily launches in real-time, follows redirects to real company websites, discovers founder/team emails, Discord/Twitter/GitHub links, detects marketing pixels (Meta Pixel, Google Analytics, TikTok Pixel), and calculates an automated **Startup Lead Score** with custom B2B outreach pitch hooks.

---

## 🚀 Why Use This Actor Over Generic Scrapers?

Most Product Hunt scrapers only extract the surface-level upvote count and discussion comments. **That data alone doesn't close sales deals or book meetings.**

When a startup launches on Product Hunt, their founders are actively sitting in front of their screens, monitoring analytics and looking for ways to scale traction. This actor gives sales agencies, recruiters, freelancers, and growth hackers the exact data needed to run **day-of-launch outreach campaigns that convert at 25–40%**.

### Feature Comparison Matrix

| Feature | Standard Apify Scrapers | **Our Maker Leads Enricher** |
| :--- | :---: | :---: |
| **Real-Time Daily Launches** | ✅ Yes | ✅ Yes (RSS Atom Feed) |
| **Maker / Hunter Identification** | ⚠️ Partial | ✅ Yes |
| **Real Startup Website Resolution** | ❌ No | ✅ Yes (Follows 301/302 redirects) |
| **Contact Email Extraction** | ❌ No | ✅ Yes (`hello@`, `team@`, etc.) |
| **Social Media Profiles** | ❌ No | ✅ Yes (Twitter/X, GitHub, Discord, LinkedIn) |
| **Ad Pixel Detection** | ❌ No | ✅ Yes (Meta Pixel, TikTok, GA4 / GTM) |
| **Missing Pixels Detection** | ❌ No | ✅ Yes (Identifies marketing gaps) |
| **AI Agency Pitch Angle** | ❌ No | ✅ Yes (Ready-to-send personalized hook) |
| **Lead Readiness Score (0–100)** | ❌ No | ✅ Yes (`startupLeadScore`) |
| **Pricing** | \$30–\$50/mo flat rental | **\$0.002 per enriched lead** (Pay-Per-Event) |

---

## 💡 Top Use Cases

1. **Digital Marketing & Paid Media Agencies:**
   - Filter newly launched startups that have Google Analytics but **lack Meta Pixel or TikTok Pixel**.
   - Send hyper-personalized pitches: *"Saw your launch today! Noticed you have 2,000+ launch visitors landing on your site but haven't installed Meta Pixel to retarget them before they leave forever..."*
2. **Designers & Web Development Studios:**
   - Target newly launched MVPs and AI SaaS products for UI/UX redesigns, speed optimization, and landing page conversions.
3. **VC & Angel Investor Scouting:**
   - Track high-velocity daily launches, founder names, and contact channels before competitors discover them.
4. **B2B SaaS Sales Reps (SDRs/BDRs):**
   - Automatically pipe hot leads into your CRM (HubSpot, Salesforce, Smartlead, Instantly) via webhooks or n8n workflows.

---

## 📥 Input Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `maxItems` | Integer | Yes | `50` | Maximum number of launches to process (1 to 100). |
| `enrichWebsites` | Boolean | No | `true` | When enabled, visits startup landing pages to extract contact info & ad pixels. |
| `filterKeywords` | Array | No | `[]` | Optional keywords to filter launches (e.g. `["AI", "SaaS", "Design"]`). |

### Sample Input JSON
```json
{
  "maxItems": 25,
  "enrichWebsites": true,
  "filterKeywords": ["AI", "Automation", "Developer"]
}
```

---

## 📤 Output Data Format

Each record in the dataset contains comprehensive firmographic and contact intelligence:

```json
{
  "productTitle": "ToDo.is",
  "tagline": "Write a to-do and your AI agent gets it done",
  "makerName": "Zac Zuo",
  "productHuntUrl": "https://www.producthunt.com/products/todo-is",
  "publishedAt": "2026-10-15T17:10:20-07:00",
  "websiteUrl": "https://todo.is",
  "emails": [
    "hello@todo.is"
  ],
  "phoneNumbers": [],
  "socials": {
    "twitter": "https://x.com/todois_ai",
    "discord": "https://discord.gg/todois"
  },
  "installedPixels": [
    "Google Analytics/GTM"
  ],
  "missingPixels": [
    "Meta Pixel",
    "TikTok Pixel"
  ],
  "startupLeadScore": 85,
  "agencyPitchAngle": "Saw ToDo.is launched on Product Hunt ('Write a to-do and your AI agent gets it done'). You're tracking traffic with Google Analytics, but missing Meta Pixel retargeting—retargeting your launch day visitors could easily double day-1 activation."
}
```

---

## 💻 Integration & SDK Usage

### Python (using `apify-client`)
```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")

# Run the actor
run = client.actor("mamang_warkop/product-hunt-launches-and-maker-leads-scraper").call(
    run_input={
        "maxItems": 30,
        "enrichWebsites": True
    }
)

# Fetch all enriched leads
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"Product: {item['productTitle']} | Email: {item['emails']} | Score: {item['startupLeadScore']}")
    print(f"Pitch Hook: {item['agencyPitchAngle']}\n")
```

### Node.js (using `apify-client`)
```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({
    token: 'YOUR_APIFY_TOKEN',
});

const run = await client.actor('mamang_warkop/product-hunt-launches-and-maker-leads-scraper').call({
    maxItems: 25,
    enrichWebsites: true,
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(`Extracted ${items.length} enriched startup leads!`);
```

---

## 💰 Fair & Transparent Pricing

- **Pay-Per-Event:** **\$0.002 per enriched startup lead**.
- Running 50 leads costs only **\$0.10**.
- Fully covered by Apify's **\$5 free monthly credits** (you can run 2,500 startup lookups every month for free!).

---

## 🛡️ Stability & Anti-Bot Protection

- Uses official RSS syndication protocols combined with smart async HTTP redirection.
- Automatic rate-limit throttling and timeout handling.
- Zero headless browser overhead for ultra-low compute unit (CU) consumption.
