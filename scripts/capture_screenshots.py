"""
Automated Screenshot Capture Script for Indian Constitution Legal AI Assistant.
Uses Playwright to interact with the running Streamlit UI and capture all 8 required genuine screenshots.
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("docs/assets/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

APP_URL = "http://localhost:8501"

def capture_all():
    print(f"[*] Starting screenshot capture from {APP_URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 960},
            device_scale_factor=1.25,
        )
        page = context.new_page()

        print("[*] Navigating to Streamlit app...")
        page.goto(APP_URL, timeout=60000)
        page.wait_for_selector(".main-title", timeout=60000)
        time.sleep(3)
        print("[+] Page loaded successfully!")

        # -------------------------------------------------------------
        # Screenshot 1: Main application screen (01_home.png)
        # -------------------------------------------------------------
        print("[*] Capturing 01_home.png...")
        page.screenshot(path=str(OUTPUT_DIR / "01_home.png"))
        print("[+] Saved 01_home.png")

        # -------------------------------------------------------------
        # Screenshot 2: Example constitutional question input (02_question_input.png)
        # -------------------------------------------------------------
        print("[*] Filling sample question...")
        input_el = page.locator("input[type='text']").first
        sample_q = "What did the Supreme Court rule regarding the Right to Privacy under Article 21 in the Puttaswamy judgment?"
        input_el.fill(sample_q)
        time.sleep(1)

        print("[*] Capturing 02_question_input.png...")
        page.screenshot(path=str(OUTPUT_DIR / "02_question_input.png"))
        print("[+] Saved 02_question_input.png")

        # -------------------------------------------------------------
        # Submit query and wait for execution
        # -------------------------------------------------------------
        print("[*] Submitting query to RAG Pipeline...")
        input_el.press("Enter")
        page.wait_for_selector(".agent-badge", timeout=90000)
        time.sleep(4)

        # -------------------------------------------------------------
        # Screenshot 3: Answer with retrieved evidence and citations (03_answer_and_citations.png)
        # -------------------------------------------------------------
        print("[*] Capturing 03_answer_and_citations.png...")
        page.screenshot(path=str(OUTPUT_DIR / "03_answer_and_citations.png"))
        print("[+] Saved 03_answer_and_citations.png")

        # -------------------------------------------------------------
        # Screenshot 4: NLP Inspector (04_nlp_inspector.png)
        # -------------------------------------------------------------
        print("[*] Expanding NLP Pipeline Inspector...")
        inspector_expander = page.locator("text=10-Stage NLP Pipeline Diagnostic Inspector").first
        if inspector_expander.is_visible():
            inspector_expander.scroll_into_view_if_needed()
            inspector_expander.click()
            time.sleep(3)
        
        print("[*] Capturing 04_nlp_inspector.png...")
        page.screenshot(path=str(OUTPUT_DIR / "04_nlp_inspector.png"))
        print("[+] Saved 04_nlp_inspector.png")

        # -------------------------------------------------------------
        # Screenshot 6: Landmark Case Comparator (06_case_comparator.png)
        # -------------------------------------------------------------
        print("[*] Navigating to Case Comparator tab...")
        page.locator("text=Case Comparator").first.click()
        time.sleep(4)
        print("[*] Capturing 06_case_comparator.png...")
        page.screenshot(path=str(OUTPUT_DIR / "06_case_comparator.png"))
        print("[+] Saved 06_case_comparator.png")

        # -------------------------------------------------------------
        # Screenshot 7: Constitution & Cases Database Explorer (07_database_explorer.png)
        # -------------------------------------------------------------
        print("[*] Navigating to Database Explorer tab...")
        page.locator("text=Constitution & Cases Database").first.click()
        time.sleep(4)
        print("[*] Capturing 07_database_explorer.png...")
        page.screenshot(path=str(OUTPUT_DIR / "07_database_explorer.png"))
        print("[+] Saved 07_database_explorer.png")

        # -------------------------------------------------------------
        # Screenshot 5: Evaluation Dashboard (05_evaluation_dashboard.png)
        # -------------------------------------------------------------
        print("[*] Navigating to Empirical Research Dashboard tab...")
        page.locator("text=Empirical Research Dashboard").first.click()
        time.sleep(5)  # Wait for charts and metrics to render
        print("[*] Capturing 05_evaluation_dashboard.png...")
        page.screenshot(path=str(OUTPUT_DIR / "05_evaluation_dashboard.png"))
        print("[+] Saved 05_evaluation_dashboard.png")

        # -------------------------------------------------------------
        # Screenshot 8: Abstention Example (08_abstention_example.png)
        # -------------------------------------------------------------
        print("[*] Navigating back to Ask Assistant tab for out-of-scope query...")
        page.locator("text=Ask Assistant & RAG Query").first.click()
        time.sleep(2)

        input_el = page.locator("input[type='text']").first
        input_el.fill("What is the penalty and procedure for dishonour of cheques under Section 138 of Negotiable Instruments Act?")
        time.sleep(1)
        input_el.press("Enter")

        print("[*] Waiting for abstention notice...")
        page.wait_for_selector("text=System Refusal / Abstention Notice", timeout=90000)
        time.sleep(3)

        print("[*] Capturing 08_abstention_example.png...")
        page.screenshot(path=str(OUTPUT_DIR / "08_abstention_example.png"))
        print("[+] Saved 08_abstention_example.png")

        browser.close()
        print("[+] All 8 screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
