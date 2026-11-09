---
name: screen-perception
description: Methodology and toolchain for multi-modal screen perception, coordinate mapping, and Linux AT-SPI accessibility inspection.
---

# Screen Perception & Coordinate Mapping Skill

এই স্কিলটি স্ক্রিনের ভিজ্যুয়াল অবস্থা অনুধাবন করা, UI এলিমেন্ট লোকেট করা এবং সঠিক কো-অর্ডিনেট নির্ধারণের ধাপগুলো বর্ণনা করে।

## ১. হাই-স্পিড ফ্রেম ক্যাপচার (Screen Capture)
* পাইথন `mss` লাইব্রেরি ব্যবহার করে মিলিসেকেন্ডের মধ্যে যেকোনো নির্দিষ্ট ডিসপ্লের (`:0` বা `:99`) ফুল রেজোলিউশন ফ্রেম ক্যাপচার করা।
* ইমেজকে VLM ফ্রেন্ডলি রেজোলিউশনে কনভার্ট করে গ্রিড ওভারলে অথবা বাউন্ডিং বক্স প্রেডিকশনে পাঠানো।

## ২. লিনাক্স AT-SPI এক্সেসিবিলিটি ট্রাভার্সাল (AT-SPI Tree Inspection)
* স্ক্রিনের বাটন এবং ইনপুট ফিল্ডের সঠিক স্থানাঙ্ক বের করার জন্য শুধুমাত্র ভিশনের ওপর নির্ভর না করে লিনাক্সের `python-atspi` বাস কুয়েরি করা:
  - উইন্ডোর নাম
  - রোল (PushButton, Entry, Text, Window, MenuBar)
  - সঠিক বাউন্ডিং বক্স স্থানাঙ্ক `(x, y, width, height)`
* এটি ১০০% নির্ভুলভাবে টেক্সট বক্স বা সাবমিট বাটনের সেন্টার পয়েন্ট এনে দেয়।

## ৩. নরম্যালাইজড কো-অর্ডিনেট থেকে পিক্সেল কনভার্সন
VLM যখন $0 \le x, y \le 1000$ রেঞ্জে কো-অর্ডিনেট পাঠায়, তখন স্ক্রিন রেজোলিউশন ($W \times H$) দিয়ে তা পিক্সেলে রূপান্তর করতে হবে:
$$X_{target} = \frac{x_{model}}{1000} \times W, \quad Y_{target} = \frac{y_{model}}{1000} \times H$$
