import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException

def scrape_links(url, max_clicks=20):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Uncomment to run headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Lỗi khởi tạo WebDriver: {e}")
        print("Hãy đảm bảo ChromeDriver đã được cài đặt và đường dẫn được cấu hình đúng.")
        return

    extracted_data = []
    seen_links = set()  # <-- NEW: track unique links
    wait_short = WebDriverWait(driver, 10)
    wait_long = WebDriverWait(driver, 15)

    try:
        print(f"Đang truy cập URL: {url}")
        driver.get(url)
        time.sleep(2)

        load_more_button_selector = "button.btn.btn-primary.control__loadmore"
        print(f"Bắt đầu tìm và nhấp nút 'Xem thêm' (tối đa {max_clicks} lần)...")
        click_count = 0
        for i in range(max_clicks):
            try:
                load_more_button = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_button_selector)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                time.sleep(0.5)
                load_more_button.click()
                click_count += 1
                print(f"Đã nhấp nút 'Xem thêm' lần {click_count}/{max_clicks}. Đang chờ tải nội dung...")
                time.sleep(3)
            except (NoSuchElementException, TimeoutException):
                print(f"Không tìm thấy nút 'Xem thêm' hoặc nút không khả dụng sau lần nhấp thứ {click_count}. Dừng nhấp.")
                break
            except ElementClickInterceptedException:
                print("Nút 'Xem thêm' bị che khuất, thử cuộn và nhấp lại...")
                driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(2)
            except Exception as e:
                print(f"Đã xảy ra lỗi khi nhấp nút 'Xem thêm' lần {click_count + 1}: {e}")
                break
        else:
            print(f"Đã hoàn thành {max_clicks} lần nhấp nút 'Xem thêm' (hoặc nút đã biến mất).")

        print("Đã nhấp xong 'Xem thêm'. Bắt đầu trích xuất ID và đường dẫn (link)...")

        link_selector = ".box-content.content-list a.cms-link"
        container_selector = ".box-content.content-list"

        try:
            print(f"Đang chờ sự xuất hiện của ít nhất một phần tử '{container_selector}'...")
            wait_long.until(EC.presence_of_element_located((By.CSS_SELECTOR, container_selector)))
            print(f"Đã tìm thấy container '{container_selector}'. Chờ các link bên trong...")
            time.sleep(1)

            link_elements = driver.find_elements(By.CSS_SELECTOR, link_selector)
            print(f"Tìm thấy tổng cộng {len(link_elements)} phần tử khớp với '{link_selector}'.")

            count = 0
            link_id_counter = 1

            for i, link_element in enumerate(link_elements):
                try:
                    link = link_element.get_attribute('href')
                    if link:
                        link_clean = link.strip()
                        if link_clean and link_clean not in seen_links:
                            seen_links.add(link_clean)  # <-- NEW: add to set
                            extracted_data.append({"id": link_id_counter, "link": link_clean})
                            link_id_counter += 1
                            count += 1
                        else:
                            print(f"  Bỏ qua link trùng: {link_clean}")
                except StaleElementReferenceException:
                    print(f"  Cảnh báo: Bỏ qua StaleElementReferenceException cho link thứ {i}.")
                    continue
                except Exception as e_inner:
                    print(f"  Lỗi khi trích xuất link thứ {i}: {e_inner}")

            print(f"Đã trích xuất thành công {count} cặp ID/đường dẫn hợp lệ.")

        except TimeoutException:
            print(f"Không tìm thấy phần tử nào khớp với '{link_selector}' hoặc container '{container_selector}' sau khi chờ.")
        except Exception as e:
            print(f"Lỗi trong quá trình tìm và trích xuất các phần tử link: {e}")

    except TimeoutException:
        print(f"Không thể tải trang {url} trong thời gian chờ.")
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn trong quá trình chạy: {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
            print("Đã đóng trình duyệt.")

    if extracted_data:
        try:
            with open('link.json', 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=4)
            print(f"Đã lưu {len(extracted_data)} cặp ID/đường dẫn vào file link.json")
        except IOError as e:
            print(f"Lỗi khi ghi file JSON: {e}")
    else:
        print("Không có dữ liệu nào được trích xuất để lưu vào file JSON.")

# --- Sử dụng hàm ---
target_url = "https://www.tinnhanhchungkhoan.vn/chung-khoan/"
number_of_clicks = 500

if target_url == "YOUR_WEBSITE_URL_HERE":
    print("Vui lòng thay thế 'YOUR_WEBSITE_URL_HERE' bằng URL thực tế của trang web bạn muốn quét.")
else:
    scrape_links(target_url, max_clicks=number_of_clicks)
