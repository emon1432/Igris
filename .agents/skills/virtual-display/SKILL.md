---
name: virtual-display
description: Guide and runbook to spawn, manage, and isolate GUI applications on an Xvfb virtual framebuffer display on Linux.
---

# Virtual Display Management Skill (Xvfb)

এই স্কিলটি লিনাক্স সিস্টেমে অদৃশ্য ভার্চুয়াল ডিসপ্লে (`DISPLAY=:99`) তৈরি, পরিচালনা এবং ক্লিনআপ করার নির্দেশনা প্রদান করে, যার মাধ্যমে মূল ব্যবহারকারীর স্ক্রিন অক্ষত রেখে ব্যাকগ্রাউন্ডে সম্পূর্ণ GUI অটোমেশন চালানো যায়।

## ১. ভার্চুয়াল ডিসপ্লে শুরু করা (Starting Virtual Display)

```bash
# Xvfb ডিসপ্লে ৯৯ তৈরি করুন (1920x1080 রেজোলিউশন ও 24-bit কালার)
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
```

## ২. ভার্চুয়াল ডিসপ্লেতে অ্যাপ রান করা (Launching Apps)

যেকোনো সফটওয়্যার এই ভার্চুয়াল ডিসপ্লেতে রান করতে হলে কমান্ডের শুরুতে `DISPLAY=:99` যুক্ত করতে হবে:
```bash
DISPLAY=:99 google-chrome-stable --no-sandbox &
DISPLAY=:99 whatsapp-for-linux &
```

## ৩. ভার্চুয়াল স্ক্রিনের স্ক্রিনশট নেওয়া (Capturing Virtual Frames)

```bash
# ImageMagick বা xwd দিয়ে ভার্চুয়াল স্ক্রিনের বর্তমান স্টেট ক্যাপচার করা
import -window root -display :99 /tmp/virtual_frame.png
```

## ৪. ভার্চুয়াল স্ক্রিনে ইনপুট প্রদান (Input Injection)

```bash
# নির্দিষ্ট ডিসপ্লেতে মাউস বা কিবোর্ড ইভেন্ট পাঠানো
xdotool -display :99 mousemove 500 400 click 1
xdotool -display :99 type "Hello Naeem"
```

## ৫. ক্লিনআপ (Termination)

```bash
# টাস্ক শেষে বা সার্ভার বন্ধ করার সময় প্রসেস ক্লিনআপ
killall Xvfb
```
