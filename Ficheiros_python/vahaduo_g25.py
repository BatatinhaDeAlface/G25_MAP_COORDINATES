import asyncio
import pandas as pd
import os
from playwright.async_api import async_playwright

# Ficheiros e variáveis de ambiente
samples_file = "MAPG25_SAMPLES.txt"
target_sample = os.getenv("TARGET_SAMPLE", "")
target_coords = os.getenv("TARGET_COORDS", "")
output_csv    = os.getenv("OUTPUT_CSV", "distancesG25.csv")

async def main():
    async with async_playwright() as p:
        # 🔹 Headless para evitar problemas em Colab ou servers
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://vahaduo.github.io/vahaduo/")

        # 1️⃣ Upload do ficheiro Source
        await page.locator("input#localfiles").set_input_files(samples_file)
        await page.wait_for_timeout(1500)

        # 2️⃣ Abrir o ficheiro carregado (MAPG25 SAMPLES)
        await page.get_by_role("button", name="MAPG25 SAMPLES").click()
        await page.wait_for_timeout(500)

        # 3️⃣ Clicar no botão "source" correto (o segundo geralmente é o certo)
        buttons_source = page.locator("button:has-text('source')")
        await buttons_source.nth(1).wait_for(state="visible")
        await buttons_source.nth(1).click()

        # 4️⃣ Abrir a aba Target
        button_target = page.locator("button:has-text('target')").nth(0)
        await button_target.click()

        # 5️⃣ Preencher o target
        target_textarea = await page.wait_for_selector("textarea#target", state="visible")
        await target_textarea.fill(f"{target_sample},{target_coords}")

        # 6️⃣ Rodar cálculo de distâncias
        await page.locator("button:has-text('distance')").nth(0).click()
        await page.wait_for_timeout(500)

        # 7️⃣ Ajustar distância máxima
        dist_input = page.locator("input#distmaxout")
        await dist_input.fill("400")
        await page.wait_for_timeout(300)

        # 8️⃣ Clicar no botão da amostra Target
        button_target_sample = page.locator(f"button:has-text('{target_sample}')").nth(0)
        await button_target_sample.wait_for(state="visible")
        await button_target_sample.click()

        # 9️⃣ Esperar resultados e capturar tabela
        await page.wait_for_selector("#distanceoutput", state="visible", timeout=60000)
        cells = page.locator("#distanceoutput td")
        n = await cells.count()
        results = []

        for i in range(0, n, 2):
            dist = await cells.nth(i).inner_text()
            pop = await cells.nth(i+1).inner_text()
            results.append((dist, pop))

        # 🔹 Salvar CSV
        df = pd.DataFrame(results, columns=["Distance","Population"])
        df.to_csv(output_csv, index=False, encoding="utf-8")
        print(f"✅ Arquivo '{output_csv}' criado com sucesso!")

        await browser.close()

asyncio.run(main())




