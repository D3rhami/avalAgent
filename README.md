![Icon](https://github.com/D3rhami/avalai-agent/blob/versions/icon.jpg)

🎃 [To change the language to English click here.](https://github.com/D3rhami/avalai-agent/blob/versions/README_EN.md)

# AvalAgent 1.0.4

یک کلاینت پایتون برای تعامل با مدل‌های هوش مصنوعی از طریق API سازگار با OpenAI شرکت AvalAI، با ویژگی‌هایی مانند تلاش‌های مجدد خودکار، پشتیبانی از مدل‌های جایگزین، حافظهٔ مکالمه، بهبود پرسش‌ها و مدیریت خطاهای قوی.

## ویژگی‌ها

* 🚀 **پشتیبانی از چندین مدل**: قابل استفاده با GPT-4o، DeepSeek، Claude-3 و سایر مدل‌های پشتیبانی‌شده توسط AvalAI
* 🔄 **تلاش‌های مجدد خودکار و پشتیبانی از مدل‌های جایگزین**: در صورت عدم موفقیت مدل اصلی، به مدل‌های ثانویه مراجعه می‌کند
* 🧠 **حافظهٔ مکالمه**: حفظ زمینهٔ گفتگو در تعاملات (قابل تنظیم)
* 💾 **ذخیره‌سازی حافظه**: امکان ذخیره و بارگذاری تاریخچهٔ مکالمات در دیسک
* 🛠️ **بهبود پرسش‌ها**: تبدیل پرسش‌های خام به پرسش‌های ساختاریافته و بهینه
* 🔒 **مدیریت ایمن کلید API**: استفاده از `SecretStr` برای حفاظت از کلید API
* 📝 **ثبت گزارش داخلی**: ثبت گزارش‌های دقیق برای اشکال‌زدایی و نظارت بر درخواست‌های API
* ⚡ **یکپارچه‌سازی با LangChain**: سازگار با فرمت‌های پیام LangChain
* 📊 **نظارت بر اعتبار مصرفی**: بررسی میزان استفاده و اعتبار باقی‌مانده از API

## نصب

```bash
pip install avalAgent
```



## استفادهٔ پایه

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# مقداردهی اولیه با کلید API
agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# دریافت پاسخ
response = agent.get_response(
    system_prompt="شما یک دستیار مفید هستید.",
    query="محاسبات کوانتومی را به زبان ساده توضیح بده"
)

print(response)
```



## مثال‌ها

### مثال ۱: استفاده با تنظیمات پیش‌فرض

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

response = agent.get_response(
    system_prompt="شما یک دستیار مفید هستید.",
    query="نظریهٔ نسبیت را توضیح بده"
)

print(response)
```



### مثال ۲: سفارشی‌سازی لیست اولویت مدل‌ها و تعداد تلاش‌ها

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    model_priority_list=[
        "gpt-4o",
        "deepseek-chat",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ],
    stop_after_attempt=5
)

response = agent.get_response(
    system_prompt="شما یک کارشناس فنی هستید.",
    query="بلاک‌چین چگونه کار می‌کند؟",
    model="gpt-4o",
    temperature=0.2
)

print(response)
```



### مثال ۳: استفاده از حافظهٔ مکالمه

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# مقداردهی اولیه با حافظه فعال
agent = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    max_memory_size=5
)

# پرسش اول برای ایجاد زمینه
response1 = agent.get_response(
    system_prompt="شما یک دستیار سفر هستید.",
    query="جاذبه‌های گردشگری پاریس را معرفی کن"
)

# پرسش دوم با بهره‌گیری از حافظه
response2 = agent.get_response(
    query="کدام‌یک برای کودکان مناسب هستند؟"
)

print(response2)
```



### مثال ۴: حافظهٔ پایدار بین جلسات

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# جلسهٔ اول - ذخیرهٔ حافظه
agent1 = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    persist_memory=True,
    memory_file="travel_chat.json"
)

response = agent1.get_response(
    system_prompt="شما یک دستیار سفر هستید.",
    query="بهترین موزه‌های لندن کدام‌اند؟"
)

# جلسهٔ دوم - بارگذاری حافظهٔ قبلی
agent2 = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    persist_memory=True,
    memory_file="travel_chat.json"
)

# ادامهٔ گفتگو
response = agent2.get_response(
    query="کدام‌یک ورودی رایگان دارند؟"
)

print(response)
```



### مثال ۵: بهبود پرسش برای پست اینستاگرام

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

raw_prompt = """
من به یک کپشن فارسی برای اینستاگرام نیاز دارم برای مجموعهٔ جدید کیف‌های لوکس ما.
کپشن باید:
- شامل ۲ تا ۳ پاراگراف کوتاه باشد
- از ایموجی‌ها به‌صورت مناسب استفاده کند
- بر روی هنر ساخت تأکید کند
- شامل یک فراخوان برای اقدام باشد
- لحن دوستانه اما شیک داشته باشد
"""

enhanced_prompt = agent.enhance_prompt(raw_prompt)
print(enhanced_prompt)

# سپس استفاده از پرسش بهبود یافته
response = agent.get_response(
    system_prompt=enhanced_prompt,
    query="۳ گزینهٔ کپشن تولید کن"
)
print(response)
```



### مثال ۶: نظارت بر اطلاعات اعتبار

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# گزینه ۱: فقط دریافت داده
credit_data = agent.get_credit_info()

# گزینه ۲: ثبت جدول فرمت‌شده
agent.log_credit_info_table()
```



## به‌روزرسانی: نسخهٔ 1.0.4

### ویژگی‌های جدید

* **بهبود پرسش**: متد جدید `enhance_prompt()` برای تبدیل پرسش‌های خام به فرمت‌های ساختاریافته
* **بهبود مدیریت خطا**: اعتبارسنجی قوی‌تر و پیام‌های خطای دقیق‌تر
* **پیکربندی JSON**: پشتیبانی از پیکربندی مبتنی بر JSON در بهبود پرسش([Sider][1])

### بهبودها

* **تغییرات API**:

  * `get_response()` اکنون از پارامترهای `**config` به‌جای آرگومان‌های جداگانه استفاده می‌کند
  * اعتبارسنجی پارامترها به‌صورت یکنواخت در تمام متدها
* **مدیریت حافظه**:

  * بهبود در مدیریت موارد خاص در ذخیره‌سازی حافظه

### تغییرات

* **تغییرات رفتاری**:

  * `get_response()` اکنون به‌جای ایجاد خطا برای پرسش‌های خالی، `None` برمی‌گرداند
  * اعتبارسنجی سخت‌گیرانه‌تر در `create_structured_prompt()`
* **مستندسازی**:

  * افزودن راهنمای فارسی
  * مستندسازی دقیق‌تر پارامترها

## پشتیبانی از مدل‌ها

مدل‌های سازگار با OpenAI که از طریق API AvalAI در دسترس هستند.
 
[مدل های پشتیبانی شده در اینجا ببنید](https://docs.avalai.ir/fa/models/index) .


## مدیریت خطا

این عامل به‌صورت خودکار:

* تلاش‌های ناموفق را تا ۳ بار تکرار می‌کند (به‌صورت پیش‌فرض)
* در صورت عدم موفقیت مدل اصلی، به مدل‌های جایگزین مراجعه می‌کند
* با محدودیت‌های نرخ و خطاهای شبکه به‌صورت مؤثر برخورد می‌کند
* گزارش‌های دقیق برای اشکال‌زدایی فراهم می‌کند

## 🐞 مشکلات و پشتیبانی

اگر باگ یا درخواست ویژگی دارید، لطفاً یک issue در [اینجا](https://github.com/D3rhami/avalai-agent/issues) باز کنید.

## LICENSE

مجوز MIT - برای جزئیات بیشتر به فایل [LICENSE](LICENSE) مراجعه کنید.
