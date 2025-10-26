# 🧾 API Automation — Creation & Post Receipts

This project demonstrates **end-to-end API automation** combining **data extraction**, **receipt creation**, **payment verification**, **PDF download**, and **database synchronization**.  

It is part of a production-level automation system. Some endpoints and credentials are secured. Not intended for direct execution.

---

## 🚀 Project Overview

The automation pipeline includes:

- ✅ Fetching receipt data from the database for selected users and court types  
- ✅ Automated **receipt creation** via secured API endpoints  
- ✅ **Status verification** of existing receipts using asynchronous API checks  
- ✅ **PDF download automation** for successfully created and paid receipts  
- ✅ **Excel reporting** for successful and failed operations  
- ✅ **Database synchronization** with full status tracking  
- ✅ **Error handling and structured logging** for better traceability  

---

## 🛠️ Tech Stack

| Tool / Library         | Purpose |
|------------------------|----------|
| **Python 3.x**         | Core programming language |
| **SQLAlchemy**         | ORM for database interaction and transaction control |
| **Requests**           | API communication for synchronous receipt creation |
| **Aiohttp / Asyncio**  | Asynchronous API calls for payment checking and PDF downloads |
| **Pandas**             | Excel data parsing and preprocessing |
| **OpenPyXL**           | Writing reports and audit logs to Excel |
| **Logging**            | Centralized logging with UI modal integration |
| **Custom Exceptions**  | Consistent error handling and recovery logic |

---

## 📂 Project Structure (Key Components)

| File / Class | Description |
|--------------|-------------|
| `base.py` | Core utilities for DB operations, async status checks, and shared headers |
| `GetDataDB` | Retrieves and prepares data from the database for automation |
| `CheckPaidReceipt` | Asynchronously checks payment statuses and updates the DB |
| `creation_post_receipts_civil.py` | Main module for creating receipts via API |
| `CreateReceiptAPI` | Sends POST requests to create receipts and generates Excel logs |
| `UpdateReceiptsStatus` | Updates database entries after successful creation |
| `download_created_receipts.py` | Handles downloading of created PDF receipts asynchronously |
| `DownloadCreatedReceipt` | Downloads and saves PDFs for paid receipts in parallel |
| `load_data_civil_receipt_to_db.py` | Loads and validates Excel data into the database |
| `run()` | Unified entry point for executing each automation stage |
| `ModalLogHandler` | Integrates logging with frontend/modal UI feedback |

---

## 🧪 Automation Features

- 🔁 **Async batch processing** (grouped by 10–20 receipts per block)  
- 🧮 **Dynamic business rules** (auto-calculated fees and minimum thresholds)  
- 📡 **Secure API communication** with full HTTP status control  
- 💾 **Database synchronization** after each operation (create/check/download)  
- 📊 **Excel-based reporting** for both success and failure cases  
- 🧱 **Error isolation** with retry logic and custom exception handling  
- 🧠 **Configurable execution** (user ID, receipt type, record filtering)  
- 📋 **Detailed structured logging** for CI/CD or modal integration  

---

## ⚙️ Example Automation Flow

1. **Load Data:**  
   - Import Excel data into the database (`load_data_civil_receipt_to_db.py`).

2. **Create Receipts:**  
   - Generate receipts through API calls (`creation_post_receipts_civil.py`).

3. **Check Payments:**  
   - Verify receipt payment statuses asynchronously (`base.py` → `CheckPaidReceipt`).

4. **Download PDFs:**  
   - Retrieve paid receipt PDFs and save them locally (`download_created_receipts.py`).

5. **Reporting & Logging:**  
   - Log all operations to Excel and modal UI for real-time monitoring.

---

## 🧰 Error Handling & Logging

- Centralized **logging system** with per-module handlers  
- **ModalLogHandler** for real-time UI updates  
- **Custom exceptions** for:
  - Missing database data  
  - Failed API responses  
  - Timeout or connectivity issues  
  - Validation or transaction errors  

---

## 🔮 Future Improvements

- 🧪 Integrate with **pytest** for automated regression testing  
- 🚀 Introduce **async receipt creation** to improve throughput  
- 🔐 Externalize **sensitive headers and URLs** via `.env` configuration  
- 📈 Add **summary reports and analytics dashboards**  
- ☁️ Enable CI/CD integration with structured logging export  
