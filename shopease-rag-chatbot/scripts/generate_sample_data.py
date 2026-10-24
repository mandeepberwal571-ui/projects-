"""
Script to generate realistic sample documents for ShopEase Customer Support RAG Bot.
Generates 6 documents in data/raw/:
1. FAQ.md
2. shipping_policy.txt
3. return_policy.pdf (multi-page)
4. troubleshooting_guide.docx
5. product_manual.pdf (multi-page)
6. warranty_and_support.md
"""

import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. FAQ.md (20+ Q&As)
# ---------------------------------------------------------------------------
FAQ_MD_CONTENT = """# ShopEase Customer Support - Frequently Asked Questions (FAQ)

Welcome to the ShopEase Help Center. Below are answers to the most frequently asked questions regarding our orders, payments, account management, shipping, returns, and digital support.

---

### Category 1: Orders and Modifications

#### Q1: How do I place an order on ShopEase?
To place an order, browse through our catalog or use the search bar at the top of the website or mobile app. Once you find an item you wish to purchase, select your preferred specifications (such as size, color, or model) and click "Add to Cart". When you are ready to complete your purchase, navigate to your Shopping Cart, review your items, and click "Proceed to Checkout". Enter or confirm your shipping address, choose your delivery speed, apply any promotional voucher codes, and select your preferred payment method. Click "Place Order" to finalize. You will receive an instant order confirmation email containing your 9-digit order number (e.g., #SE-9843210).

#### Q2: Can I modify or cancel my order after placing it?
Orders can be modified or cancelled within a strict 30-minute window after placement. During this window, go to "My Orders" in your account dashboard and select "Cancel Order" or "Edit Shipping Address". Once an order passes the 30-minute mark, it is automatically routed to our automated fulfillment centers for picking and packing, and modifications are no longer permitted. If you cannot cancel in time, you may refuse delivery or initiate a return within 30 days of receipt.

#### Q3: What happens if an item in my order goes out of stock after payment?
In rare instances of simultaneous inventory deduction, an item may become backordered or out of stock. If this occurs, ShopEase will notify you via email and SMS within 4 hours. You will be given two choices: wait for inventory replenishment (typically 5 to 7 business days) or receive an immediate automatic refund to your original payment method. If you select a refund, store credits will also include an additional $5 courtesy voucher towards your next purchase.

#### Q4: How do I apply a discount coupon or gift card?
During Step 2 of the checkout flow, look for the field labeled "Have a promo code or gift card?". Enter your code and click "Apply". Valid discount codes will immediately reflect in the Order Summary breakdown before payment. Please note that only one promotional coupon can be applied per order; however, ShopEase digital gift cards can be stacked with one promotional coupon and store credits.

---

### Category 2: Payments and Invoicing

#### Q5: What payment methods does ShopEase accept?
ShopEase accepts all major credit and debit cards, including Visa, MasterCard, American Express, and Discover. We also support digital wallets including Apple Pay, Google Pay, and PayPal. For eligible orders between $50 and $1,500, customers in supported regions may choose Buy-Now-Pay-Later (BNPL) through Klarna or Afterpay, splitting purchases into 4 interest-free installments paid every two weeks. We do not accept cash-on-delivery (COD) or paper checks.

#### Q6: Why was my payment declined, and what should I do?
Payment declines typically occur due to one of the following reasons:
1. Incorrect billing address: Ensure the billing ZIP/postal code entered matches the address registered with your issuing card bank.
2. 3D Secure verification timeout (`ERR_PAY_402`): Your bank failed to complete SMS OTP verification within 180 seconds.
3. Insufficient funds or daily fraud detection triggers: Contact your issuing bank to authorize transactions from ShopEase E-Commerce Inc.
4. Expired card details or incorrect CVV code (3 digits on Visa/MasterCard back, 4 digits on Amex front).

#### Q7: When will my credit card be charged?
An authorization hold for the total order amount is placed on your card at the moment you click "Place Order". Your card is only formally charged when the order packages are scanned and dispatched from our fulfillment warehouse. If an order is cancelled prior to shipment, the authorization hold typically drops off within 2 to 5 business days, depending on your bank.

#### Q8: How can I download a tax invoice for my purchase?
Commercial tax invoices with full VAT/GST breakdowns are automatically generated upon dispatch. To download an invoice, log in to your account, visit "My Orders", find the relevant order, and click "Download Tax Invoice (PDF)". Invoices can also be requested by emailing billing@shopease.com with your 9-digit order ID.

---

### Category 3: Account Security and Profile Management

#### Q9: How do I reset my account password?
If you have forgotten your password, navigate to the Sign In screen and click "Forgot Password?". Enter your registered email address or verified mobile number. We will send a secure 6-digit one-time passcode (OTP) valid for 10 minutes. Enter the OTP on the verification screen and choose a strong new password containing at least 8 characters, including one uppercase letter, one number, and one special symbol.

#### Q10: What should I do if my account is locked?
Accounts are locked automatically for 60 minutes after 5 consecutive failed login attempts, showing error code `ERR_LOGIN_105`. You can wait 60 minutes for automatic unlocking, or instantly unlock your account by verifying your identity via SMS OTP sent to your registered phone number. If you suspect unauthorized access, contact security@shopease.com immediately.

#### Q11: How do I enable Two-Factor Authentication (2FA)?
For enhanced security, we strongly recommend enabling 2FA. Go to Account Settings > Security > Two-Factor Authentication. You may choose between SMS-based authentication or Authenticator App (Google Authenticator, Microsoft Authenticator, or Authy). Scan the QR code displayed on the screen and enter the 6-digit confirmation code generated by your app.

#### Q12: Can I delete my ShopEase account and associated data?
Yes, in compliance with GDPR and CCPA regulations, you can request account deletion. Navigate to Account Settings > Privacy & Data > Delete Account. Once submitted, your account enters a 7-day grace period during which you can cancel the request by logging in. After 7 days, your account profile, saved addresses, and payment tokens will be permanently anonymized. Past order invoices will be retained for 7 years to comply with statutory legal accounting requirements.

---

### Category 4: Shipping and Tracking

#### Q13: What shipping options are available and what are the delivery timeframes?
ShopEase provides three shipping tiers within the continental United States:
- Standard Shipping: 3 to 5 business days ($4.99 flat rate, or FREE on orders of $50 or more).
- Express Delivery: 1 to 2 business days ($12.99 flat rate).
- Overnight Priority: Next business day delivery if ordered before 2:00 PM EST ($24.99 flat rate).
Delivery timeframes to Alaska, Hawaii, and Puerto Rico typically require an additional 2 to 4 business days.

#### Q14: How do I track my package?
Once your order ships, an automated tracking email is dispatched containing your carrier tracking number (FedEx, UPS, or USPS) and a direct tracking link. You can also track your shipment in real time under "My Orders" > "Track Shipment". Tracking information usually updates within 12 hours of courier pickup.

#### Q15: What should I do if tracking says "Delivered" but I haven't received my package?
If your tracking status shows delivered but you cannot locate the package:
1. Verify the delivery address listed in your order confirmation.
2. Check around potential drop-off spots, including porches, back gates, side doors, and building mailrooms.
3. Check with household members and immediate neighbors.
4. Allow 24 hours from delivery confirmation, as couriers occasionally scan parcels prematurely.
If the package has not arrived after 24 hours, contact customer support within 7 days to initiate a formal lost-transit carrier claim.

#### Q16: Do you ship internationally?
Yes, ShopEase ships to over 45 international destinations including Canada, the UK, the European Union, Australia, and Japan. International shipments take 7 to 14 business days via DHL Express. All international orders are shipped DDP (Delivered Duty Paid), meaning customs duties and import taxes are calculated and collected during checkout with zero surprise fees on delivery.

---

### Category 5: Returns, Exchanges, and Damaged Items

#### Q17: What is the ShopEase return policy window?
ShopEase offers a 30-day standard return window for most brand-new, unopened, or gently inspected items from the date of confirmed delivery. Items must be in their original packaging with all included accessories, documentation, and tags intact.

#### Q18: Are there non-returnable items?
Yes. The following categories cannot be returned due to hygiene, copyright, and safety regulations:
- Opened personal care and intimate hygiene products.
- Perishable goods, edible grocery items, and flowers.
- Downloadable digital software keys and digital gift cards.
- Custom engraved or personalized merchandise.
- Hazardous materials or items containing flammable liquids/gases.

#### Q19: What should I do if I receive a broken or defective item?
If an item arrives damaged, defective, or incorrect, you must report it within 48 hours of delivery. Navigate to "My Orders", click "Report Issue / Return", select "Item arrived damaged", and upload at least two clear photographs showing:
1. The physical damage or flaw on the product.
2. The outer shipping carton and shipping label barcode.
Our automated claims system will review the submission within 4 business hours. In most cases, a free replacement is dispatched immediately with a prepaid return shipping label for the damaged unit.

#### Q20: How long does a refund take to process?
Once our return fulfillment center receives your returned parcel, the quality control inspection takes 1 to 2 business days. Following approval, refunds are issued immediately. The funds will reflect in your account within:
- Credit/Debit Cards: 3 to 5 business days.
- PayPal / Digital Wallets: 24 to 48 hours.
- ShopEase Store Credit / Gift Balance: Instant.
"""

# ---------------------------------------------------------------------------
# 2. shipping_policy.txt
# ---------------------------------------------------------------------------
SHIPPING_POLICY_TXT_CONTENT = """SHOPEASE E-COMMERCE INC. - OFFICIAL SHIPPING & FULFILLMENT POLICY
Document Code: POL-SHP-2026-V3
Effective Date: January 1, 2026
Last Revised: October 1, 2026

1. GENERAL DISPATCH & PROCESSING OVERVIEW
At ShopEase, our commitment is to provide fast, reliable, and transparent shipping across all consumer orders. Every order placed on the ShopEase platform undergoes automated fraud verification, inventory allocation, and fulfillment dispatch.

Standard fulfillment operational hours are Monday through Friday, 7:00 AM to 6:00 PM EST, and Saturday, 8:00 AM to 2:00 PM EST. Orders placed on Sundays or official federal public holidays will begin processing on the following business day.

Orders containing in-stock items are processed and handed over to courier carriers within 12 to 24 hours of successful payment authorization. During peak seasonal promotional campaigns (such as Black Friday, Cyber Week, and Annual Prime Blowouts), warehouse processing times may extend up to 48 hours.

2. DOMESTIC SHIPPING TIERS (CONTINENTAL UNITED STATES)
ShopEase partners with tier-1 national logistics providers, including FedEx Express, United Parcel Service (UPS), and the United States Postal Service (USPS), to offer three standardized domestic delivery speeds:

Tier A: Standard Ground Shipping
- Transit Window: 3 to 5 business days following dispatch.
- Base Charge: Flat fee of $4.99 per order for cart sub-totals under $50.00.
- Free Shipping Incentive: Orders with a merchandise sub-total of $50.00 or greater (calculated after coupons and before taxes) qualify automatically for FREE Standard Shipping.
- Carrier Selection: Smart-routed between USPS Ground Advantage and UPS Ground based on destination logistics density.

Tier B: Express 2-Day Air Delivery
- Transit Window: 1 to 2 business days following dispatch.
- Base Charge: Flat fee of $12.99 per order.
- Guarantee: Delivery attempted by end of the second business day. Guaranteed Saturday delivery is included for metropolitan ZIP codes.

Tier C: Overnight Priority Delivery
- Transit Window: Guaranteed next business day delivery.
- Order Cut-Off Time: Orders must be finalized and authorized by 2:00 PM Eastern Standard Time (EST) Monday through Thursday. Orders placed after 2:00 PM on Thursday will arrive on Monday. Orders placed on Friday before 2:00 PM will arrive on Monday unless Saturday Priority ($10 surcharge) is selected.
- Base Charge: Flat fee of $24.99 per order.

3. NON-CONTINENTAL DOMESTIC REGIONS
Shipments destined for Alaska, Hawaii, Puerto Rico, Guam, and US Military APO/FPO addresses:
- Applicable Tiers: Standard Ground and Priority Mail only.
- Transit Window: 5 to 9 business days for AK, HI, and PR; up to 14 business days for APO/FPO destinations.
- Surcharge: A flat $8.50 remote logistics handling surcharge applies to all non-continental orders regardless of cart value.

4. INTERNATIONAL SHIPPING & CUSTOMS CLEARANCE (DDP)
ShopEase currently ships directly to 48 countries across North America, Europe, Asia-Pacific, and Latin America via DHL Express Worldwide and FedEx International Priority.

Delivered Duty Paid (DDP) Standards:
All international transactions are processed under Incoterms DDP rules. When completing checkout on ShopEase:
- Local import duties, Value Added Tax (VAT), Goods and Services Tax (GST), and standard customs clearance brokerage fees are calculated dynamically in real-time and added to the final checkout total.
- The recipient will NEVER be contacted by the courier or local customs agency demanding additional customs fees upon parcel delivery.
- Estimated International Transit: 6 to 10 business days for standard international; 3 to 5 business days for DHL Express Priority.
- International shipping charges vary based on volumetric weight and destination country, starting at $19.99 for Canada and $24.99 for the United Kingdom and European Union.

5. PACKAGE TRACKING & NOTIFICATIONS
Upon parcel handover to the carrier, a unique 12-to-22-character tracking identifier is generated and registered in the ShopEase tracking portal. Customers receive:
1. Automated Dispatch Email: Contains courier identity, package weight, tracking number, and live tracking hyperlink.
2. Real-time SMS Updates: Available for opt-in customers upon checkout, providing milestone alerts for "Out for Delivery", "Delayed by Weather", and "Delivered".
3. Customer Dashboard: Under the "My Orders" tab, customers can view live GPS coordinates and estimated delivery time windows provided by carrier APIs.

6. INCLEMENT WEATHER, DELAYS, AND FORCE MAJEURE
While ShopEase and our carrier partners maintain an on-time dispatch rate exceeding 98.4%, occasional unavoidable delays occur due to severe winter storms, hurricanes, national transit disruptions, or customs clearance bottlenecks. In the event of a recognized carrier delay exceeding 48 hours beyond the scheduled delivery window, customers are entitled to a full refund of any paid expedited shipping fees ($12.99 or $24.99) upon request to support@shopease.com.

7. FULFILLMENT RESTRICTIONS
- P.O. Box Addresses: Standard Shipping via USPS is required for all P.O. Box addresses. Express and Overnight air couriers (FedEx/UPS) cannot deliver to P.O. Boxes.
- Hazardous Items: Items containing lithium-ion batteries exceeding 100Wh, aerosol sprays, and chemical solvents cannot be shipped via air express or international carriers; these must ship via Ground Transport only.
"""

# ---------------------------------------------------------------------------
# 3. return_policy.pdf (Multi-page PDF via ReportLab)
# ---------------------------------------------------------------------------
def generate_return_policy_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=15,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['BodyText'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#742A2A"),
        spaceBefore=6,
        spaceAfter=10
    )

    story = []

    # PAGE 1
    story.append(Paragraph("ShopEase Returns & Refund Policy", title_style))
    story.append(Paragraph("Document Version: 4.2 | Official E-Commerce Compliance Policy", callout_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Purpose and Return Window Overview", h1_style))
    story.append(Paragraph(
        "At ShopEase, we take pride in delivering superior customer satisfaction. If you are not entirely satisfied "
        "with your purchase, our returns framework is designed to be frictionless, transparent, and prompt. "
        "Customers are granted a standard <b>30-day return window</b> commencing from the confirmed date of carrier delivery. "
        "To qualify for a standard refund, return authorization requests must be submitted through our customer portal "
        "before midnight on the 30th calendar day post-delivery.",
        body_style
    ))
    story.append(Paragraph(
        "Eligible returns must satisfy the following condition prerequisites:",
        body_style
    ))
    story.append(Paragraph("• Items must be in brand-new, unused, and resaleable condition.", bullet_style))
    story.append(Paragraph("• All original manufacturer packaging, barcodes, warranty cards, manuals, and bundled accessories must be present.", bullet_style))
    story.append(Paragraph("• Clothing and wearable apparel must retain all original tags attached, with zero evidence of washing, perfume scents, or alteration.", bullet_style))
    story.append(Paragraph("• Electronic devices must have all personal user accounts unlinked, factory reset performed, and lock passwords removed.", bullet_style))

    story.append(Paragraph("2. Non-Returnable and Restricted Merchandise", h1_style))
    story.append(Paragraph(
        "For legal safety, public health guidelines, and copyright protection standards, certain categories are classified as strictly non-returnable and non-refundable once opened or delivered:",
        body_style
    ))
    story.append(Paragraph("• <b>Hygiene & Personal Wellness:</b> In-ear headphones, electric toothbrushes, razors, personal wellness products, and intimate apparel once the tamper-evident seal is broken.", bullet_style))
    story.append(Paragraph("• <b>Consumables & Perishables:</b> Nutritional supplements, food items, beverage pods, and fresh botanicals.", bullet_style))
    story.append(Paragraph("• <b>Digital Products & Subscriptions:</b> Downloadable software licenses, gaming activation codes, and prepaid digital gift cards.", bullet_style))
    story.append(Paragraph("• <b>Personalized Goods:</b> Custom-printed apparel, custom-engraved jewelry, or bespoke assembled hardware.", bullet_style))

    story.append(Paragraph("3. Damaged, Defective, or Incorrect Deliveries (48-Hour Protocol)", h1_style))
    story.append(Paragraph(
        "In the unfortunate event that an item arrives damaged in transit, defective out of the box, or incorrect due to a picking error, "
        "ShopEase provides expedited resolution with zero return shipping costs for the customer.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Action Required within 48 Hours:</b> Customers must notify ShopEase Support within forty-eight (48) hours of confirmed carrier delivery. "
        "Failure to report physical transit damage within 48 hours limits the claim to standard manufacturer warranty channels.",
        callout_style
    ))

    # PAGE BREAK TO CREATE A MULTI-PAGE DOCUMENT
    story.append(PageBreak())

    # PAGE 2
    story.append(Paragraph("ShopEase Returns & Refund Policy (Continued)", title_style))
    story.append(Paragraph("Page 2: Resolution Procedures, Refund Timelines, and Fees", callout_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Step-by-Step Return Authorization Process", h1_style))
    story.append(Paragraph(
        "To initiate an authorized return, adhere strictly to the following procedure:",
        body_style
    ))
    story.append(Paragraph("1. Log in to your ShopEase Account and navigate to <b>'My Orders'</b>.", bullet_style))
    story.append(Paragraph("2. Locate the specific order and select <b>'Initiate Return / Exchange'</b>.", bullet_style))
    story.append(Paragraph("3. Choose the reason code from the dropdown menu (e.g., 'Incorrect Size', 'Changed Mind', 'Defective Item', 'Damaged Packaging').", bullet_style))
    story.append(Paragraph("4. If reporting damage or defect, upload at least two (2) high-resolution photographs illustrating the flaw and the courier shipping label.", bullet_style))
    story.append(Paragraph("5. Print the prepaid Return Merchandise Authorization (RMA) shipping label and the RMA packing slip.", bullet_style))
    story.append(Paragraph("6. Securely package the merchandise into a sturdy shipping box, insert the RMA packing slip inside, affix the prepaid label outside, and drop the package at any authorized UPS or FedEx drop-off location.", bullet_style))

    story.append(Paragraph("5. Restocking and Shipping Fee Schedule", h1_style))
    story.append(Paragraph(
        "Return shipping costs and applicable processing fees are governed by the classification of the return:",
        body_style
    ))

    # Table of fees
    table_data = [
        ["Return Reason", "Return Shipping Cost", "Restocking Fee", "Refund Type"],
        ["Defective or Damaged", "FREE (Prepaid by ShopEase)", "$0.00 (No fee)", "100% Full Refund or Replacement"],
        ["Incorrect Item Shipped", "FREE (Prepaid by ShopEase)", "$0.00 (No fee)", "100% Full Refund or Reshipment"],
        ["Customer Remorse / Fit", "$5.99 (Deducted from refund)", "$0.00 (No fee)", "Refund minus shipping cost"],
        ["Late Return (Day 31-45)*", "$5.99 (Deducted)", "15% Restocking Fee", "Store Credit Balance Only"]
    ]
    t = Table(table_data, colWidths=[120, 130, 110, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("6. Warehouse Inspection and Refund Disbursements", h1_style))
    story.append(Paragraph(
        "Upon physical receipt at our central returns fulfillment facility in Columbus, Ohio, our Quality Assurance team "
        "conducts a physical scan and grading within <b>48 business hours</b>. Once certified as compliant with return standards, "
        "the financial refund is triggered automatically to the original payment instrument:",
        body_style
    ))
    story.append(Paragraph("• <b>Credit and Debit Cards:</b> Financial posting within 3 to 5 business days, depending on bank settlement policies.", bullet_style))
    story.append(Paragraph("• <b>PayPal / Digital Wallets:</b> Posted within 24 business hours.", bullet_style))
    story.append(Paragraph("• <b>ShopEase Store Credits & Gift Vouchers:</b> Available instantly upon inspection sign-off.", bullet_style))
    story.append(Paragraph("• <b>Klarna / Afterpay:</b> Future scheduled installments are cancelled; paid installments are refunded by the BNPL provider within 5-7 business days.", bullet_style))

    story.append(Paragraph("7. Support Contact for Complex Claims", h1_style))
    story.append(Paragraph(
        "For special escalation inquiries or orders exceeding $1,000 in return value, contact returns-escalations@shopease.com "
        "or call our toll-free support line at 1-800-555-EASE (Option 3 for Returns).",
        body_style
    ))

    doc.build(story)

# ---------------------------------------------------------------------------
# 4. troubleshooting_guide.docx (via python-docx)
# ---------------------------------------------------------------------------
def generate_troubleshooting_guide_docx(output_path: Path):
    doc = Document()

    # Title
    title = doc.add_heading('ShopEase Platform Technical Troubleshooting & Error Code Guide', level=0)
    title.style.font.color.rgb = RGBColor(26, 54, 93)

    p_intro = doc.add_paragraph(
        "This official reference guide provides step-by-step resolution procedures for common mobile application, "
        "web platform, payment processing, and account access issues encountered by ShopEase customers and support agents."
    )
    p_intro.style.font.size = Pt(10.5)

    # Section 1
    doc.add_heading('1. Payment Processing Errors and Gateway Failures', level=1)
    
    doc.add_heading('Error Code: ERR_PAY_402 (3D Secure Authentication Timeout)', level=2)
    doc.add_paragraph(
        "Symptom: The customer experiences a spinning loading spinner on checkout, followed by a red banner displaying: "
        "'Transaction Failed: ERR_PAY_402 - 3D Secure verification could not be completed in the allotted time.'"
    )
    doc.add_paragraph(
        "Root Cause: The customer's banking institution issued an SMS One-Time Password (OTP) or mobile banking push challenge, "
        "but the customer failed to complete verification within the 180-second security window, or carrier SMS routing dropped the challenge."
    )
    doc.add_paragraph("Resolution Steps for Agent and Customer:")
    doc.add_paragraph("1. Verify that the customer has active cellular reception and can receive bank SMS messages.", style='List Bullet')
    doc.add_paragraph("2. Ensure pop-up blockers or aggressive browser ad-blockers are disabled, as they can prevent the bank's 3D Secure modal from rendering.", style='List Bullet')
    doc.add_paragraph("3. Advise the customer to clear browser cache and cookies, or attempt the purchase in an Incognito / Private window.", style='List Bullet')
    doc.add_paragraph("4. If the error repeats, recommend an alternative payment method such as PayPal, Apple Pay, or a different credit card.", style='List Bullet')

    doc.add_heading('Error Code: ERR_PAY_501 (Payment Gateway Authorization Declined)', level=2)
    doc.add_paragraph(
        "Symptom: The order fails immediately with 'ERR_PAY_501: Your payment was declined by the card processor.'"
    )
    doc.add_paragraph(
        "Root Cause: The issuing bank declined the charge due to incorrect billing zip code, CVV mismatch, or automated anti-fraud security triggers for unusual transaction sizes."
    )
    doc.add_paragraph("Resolution Steps:")
    doc.add_paragraph("1. Re-enter card details, paying careful attention to the 3-digit CVV and the registered postal code.", style='List Bullet')
    doc.add_paragraph("2. Contact card issuing bank to authorize transactions originating from merchant 'ShopEase E-Commerce LLC'.", style='List Bullet')

    # Section 2
    doc.add_heading('2. Account Access and Authentication Errors', level=1)

    doc.add_heading('Error Code: ERR_LOGIN_105 (Account Locked due to Rate Limiting)', level=2)
    doc.add_paragraph(
        "Symptom: Customer is unable to log in and sees error: 'Account Temporarily Locked: ERR_LOGIN_105. Please try again later or contact support.'"
    )
    doc.add_paragraph(
        "Root Cause: The ShopEase security firewall detected 5 consecutive incorrect password submissions within a 15-minute window, activating a safety lockout to prevent credential stuffing and brute-force attacks."
    )
    doc.add_paragraph("Resolution Steps:")
    doc.add_paragraph("1. Automatic Cooldown: The account will automatically unlock after exactly 60 minutes.", style='List Bullet')
    doc.add_paragraph("2. Instant Self-Service Unlock: Click 'Forgot Password?' on the login screen. Completing the identity verification challenge via verified SMS or email OTP will instantly reset the lockout counter.", style='List Bullet')
    doc.add_paragraph("3. Agent Unlock Protocol: Support agents can verify customer identity using three profile security questions and initiate a manual unlock token from the admin console.", style='List Bullet')

    doc.add_heading('Error Code: ERR_AUTH_204 (Session Token Expiration)', level=2)
    doc.add_paragraph(
        "Symptom: When clicking 'Place Order' or 'View Account', the app redirects to the sign-in screen without completing the action."
    )
    doc.add_paragraph(
        "Fix: The JSON Web Token (JWT) session has expired (sessions expire after 14 days of inactivity, or immediately upon password changes on another device). "
        "Log out completely, force-close the mobile application, reopen, and log back in."
    )

    # Section 3
    doc.add_heading('3. Mobile Application Crashes and Cart Synchronization', level=1)
    doc.add_paragraph(
        "When customers report that cart items disappear, items will not add to cart, or the app crashes during navigation, follow this standard troubleshooting triage:"
    )
    doc.add_paragraph("Step 1: Check App Version. Verify the customer is running ShopEase App version 4.12.0 or higher. Older builds (prior to v4.10) have deprecated API endpoints.", style='List Bullet')
    doc.add_paragraph("Step 2: Clear Application Cache (Android). Go to Device Settings > Apps > ShopEase > Storage & Cache > Clear Cache.", style='List Bullet')
    doc.add_paragraph("Step 3: Cart Resynchronization. If cart items are out of sync across devices, toggle 'Sync Cart Across Devices' under Account Settings > Preferences to ON.", style='List Bullet')
    doc.add_paragraph("Step 4: Network Reconnection. Switch from weak Wi-Fi to cellular data (LTE/5G) or vice versa to rule out intermittent network socket drops.", style='List Bullet')

    # Section 4
    doc.add_heading('4. Contacting Technical Engineering Escalations', level=1)
    doc.add_paragraph(
        "If a customer's issue cannot be resolved through the steps above, tier-1 agents must collect the following debugging details before opening an engineering Jira ticket:"
    )
    doc.add_paragraph("• Customer User ID and Registered Email Address", style='List Bullet')
    doc.add_paragraph("• Exact Error Code and verbatim error message", style='List Bullet')
    doc.add_paragraph("• Device model (e.g., iPhone 15 Pro, Samsung Galaxy S24) and Operating System Version", style='List Bullet')
    doc.add_paragraph("• Network type (Wi-Fi, 5G, or VPN connection)", style='List Bullet')
    doc.add_paragraph("• High-resolution screenshot or screen recording of the error state", style='List Bullet')

    doc.save(str(output_path))

# ---------------------------------------------------------------------------
# 5. product_manual.pdf (Multi-page PDF via ReportLab for SmartBand X1)
# ---------------------------------------------------------------------------
def generate_product_manual_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ManualTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'ManualSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#3182CE"),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'ManualH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'ManualBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'ManualBullet',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=15,
        spaceAfter=3
    )

    story = []

    # PAGE 1
    story.append(Paragraph("ShopEase SmartBand X1 - User Manual & Operating Guide", title_style))
    story.append(Paragraph("Model: SBX1-2026-BLK | High-Precision Fitness & Health Tracker", subtitle_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Box Contents & Hardware Overview", h1_style))
    story.append(Paragraph(
        "Congratulations on purchasing the ShopEase SmartBand X1. Your package includes the SmartBand X1 main tracking module, "
        "one hypoallergenic medical-grade silicone strap, a proprietary magnetic 2-pin USB charging cable (Length: 1.0m), and this quickstart user guide.",
        body_style
    ))
    story.append(Paragraph("Hardware Specifications:", body_style))
    story.append(Paragraph("• <b>Display:</b> 1.47-inch AMOLED color touchscreen, 194x368 resolution, 282 PPI with anti-fingerprint coating.", bullet_style))
    story.append(Paragraph("• <b>Biometric Sensors:</b> 6-axis accelerometer, optical PPG heart rate sensor, SpO2 blood oxygen sensor, and capacitive skin contact sensor.", bullet_style))
    story.append(Paragraph("• <b>Connectivity:</b> Bluetooth Low Energy (BLE 5.2) with 10-meter unobstructed operating range.", bullet_style))
    story.append(Paragraph("• <b>Water Resistance:</b> 5 ATM / IP68 certified up to 50 meters water depth (suitable for pool swimming and showering; not for scuba diving or hot saunas).", bullet_style))

    story.append(Paragraph("2. Charging & Battery Maintenance", h1_style))
    story.append(Paragraph(
        "Before first use, charge the SmartBand X1 continuously for at least 90 minutes. Connect the magnetic charging cradle "
        "to the metallic charging pins on the rear of the band module. Connect the standard USB-A plug to any certified 5V/1A or 5V/2A "
        "wall power adapter or computer USB port.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Important Charging Precautions:</b> Do not use fast-charging adapters exceeding 5V/2A (10W), as excessive voltage will degrade "
        "the 180mAh lithium-polymer battery cells. Ensure charging pins are clean and dry before docking. A full charge delivers up to "
        "12 days of typical usage, or 6 days with Continuous 24/7 Heart Rate and Always-On Display enabled.",
        body_style
    ))

    story.append(Paragraph("3. Smartphone Pairing & App Setup", h1_style))
    story.append(Paragraph(
        "The SmartBand X1 requires a smartphone running iOS 13.0 or Android 8.0 and above. Follow these steps to pair:",
        body_style
    ))
    story.append(Paragraph("1. Download the official <b>'ShopEase Fitness'</b> app from the Apple App Store or Google Play Store.", bullet_style))
    story.append(Paragraph("2. Turn on Bluetooth on your smartphone and launch the app.", bullet_style))
    story.append(Paragraph("3. Sign in with your ShopEase account credentials.", bullet_style))
    story.append(Paragraph("4. Wake the SmartBand X1 by tapping the display; a QR code will appear.", bullet_style))
    story.append(Paragraph("5. In the app, tap 'Add New Device', select 'SmartBand X1', and scan the QR code displayed on the band screen.", bullet_style))
    story.append(Paragraph("6. Confirm the Bluetooth pairing challenge on both your phone and band within 30 seconds.", bullet_style))

    # PAGE BREAK TO MAKE IT MULTI-PAGE
    story.append(PageBreak())

    # PAGE 2
    story.append(Paragraph("ShopEase SmartBand X1 - Operating Guide (Continued)", title_style))
    story.append(Paragraph("Page 2: Operations, Maintenance, Reset, and Warranty", subtitle_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. Daily Gestures and Navigation", h1_style))
    story.append(Paragraph("• <b>Swipe Up:</b> Access notifications, unread messages, and incoming call alerts.", bullet_style))
    story.append(Paragraph("• <b>Swipe Down:</b> Open the Quick Settings control center (Do Not Disturb, Flashlight, Find My Phone, Screen Brightness).", bullet_style))
    story.append(Paragraph("• <b>Swipe Left/Right:</b> Cycle through biometric widgets (Daily Activity Rings, Real-time Heart Rate, SpO2 Tracker, Weather, Music Controls).", bullet_style))
    story.append(Paragraph("• <b>Press & Hold Watchface (2 seconds):</b> Enter the watchface gallery to swap visual themes.", bullet_style))

    story.append(Paragraph("5. Troubleshooting and Factory Reset Procedures", h1_style))
    story.append(Paragraph(
        "If you encounter erratic behavior, inaccurate sensor metrics, or Bluetooth disconnection issues:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Soft Reboot:</b> Swipe Down to Quick Settings > tap the Gear icon (Settings) > tap 'Restart'. "
        "All user data and step counts for the current day will be preserved.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Hard Factory Reset:</b> To unpair and wipe all data: Settings > System > 'Factory Reset'. Confirm when prompted. "
        "The device will vibrate for 2 seconds, erase all onboard cache, and restart showing the original out-of-the-box QR pairing screen.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Unresponsive Screen Recovery:</b> If the screen is black and does not respond to touch, connect the device to the magnetic charger. "
        "While charging, press and hold the hidden recessed pinhole button located beside the charging terminal using a paperclip for 8 seconds. "
        "The device will force reboot.",
        body_style
    ))

    story.append(Paragraph("6. Cleaning, Skin Health & Safe Care", h1_style))
    story.append(Paragraph(
        "Rinse the band regularly with clean water after swimming, intense sweating, or exposure to sunscreen and lotions. "
        "Do not use abrasive chemicals, dish soap, or solvent cleaners. Dry the band thoroughly with a lint-free cloth. "
        "To avoid contact dermatitis, wear the band comfortably snug (not overly tight) allowing one finger of slack.",
        body_style
    ))

    story.append(Paragraph("7. 1-Year Limited Hardware Warranty", h1_style))
    story.append(Paragraph(
        "The ShopEase SmartBand X1 includes a <b>One (1) Year Limited Warranty</b> covering defects in materials and workmanship "
        "under normal consumer use. The warranty covers sensor failure, display malfunction, and battery capacity loss exceeding 30% "
        "within 12 months. The warranty strictly excludes accidental screen cracking, liquid damage beyond 5 ATM ratings (such as hot showers/saunas), "
        "and unauthorized third-party disassembly. For warranty service, email warranty@shopease.com with proof of purchase.",
        body_style
    ))

    doc.build(story)

# ---------------------------------------------------------------------------
# 6. warranty_and_support.md
# ---------------------------------------------------------------------------
WARRANTY_AND_SUPPORT_MD_CONTENT = """# ShopEase Warranty Policies and Customer Support Escalations
Document Reference: DOC-WRNTY-2026-REV2
Effective: January 2026

## 1. ShopEase Standard Limited Warranty (1-Year)

Every electronic device, appliance, and private-label hardware product sold directly by ShopEase is backed by our comprehensive **One (1) Year Limited Consumer Warranty**. This coverage guarantees that your product will remain free from manufacturing defects in materials, components, and assembly for a duration of 365 calendar days from the verified date of delivery.

### What is Covered:
- **Internal Component Failure:** Motherboard malfunction, Bluetooth/Wi-Fi chip dropouts, motor burnouts, and internal wiring failures under normal household use.
- **Sensor & Biometrics:** Optical sensors, touch digitizer non-responsiveness, and accelerometer inaccuracies.
- **Battery Performance:** Lithium batteries exhibiting premature degradation (defined as holding less than 70% of factory rated capacity within 12 months).
- **Firmware & Software Integrity:** Fatal firmware corruption resulting from official Over-The-Air (OTA) updates.

### What is Explicitly Excluded:
- **Accidental Damage:** Screen cracks, dents, casing fractures resulting from drops, impacts, or crush force.
- **Liquid Intrusion Beyond Rating:** Exposure to water pressures exceeding specified IP/ATM ratings, steam from saunas, immersion in saltwater, or exposure to corrosive liquids.
- **Unauthorized Repair:** Modifications, repairs, or disassembly performed by unauthorized repair shops or non-OEM components.
- **Normal Wear and Tear:** Cosmetic scratches, strap discoloration, cosmetic peeling of exterior coatings, and expected cable fraying over extended use.
- **Acts of Nature:** Damage caused by lightning strikes, power surges, floods, or residential fires.

---

## 2. ShopEase Care+ Extended Protection Plans

For customers seeking complete peace of mind, ShopEase offers optional **ShopEase Care+ Protection** available for purchase within 30 days of hardware delivery:
- **Duration:** Extends total coverage to 2 years or 3 years.
- **Accidental Damage Protection (ADH):** Includes up to two (2) accidental drop or spill claims per 12-month period subject to a nominal $29 deductible.
- **Rapid Express Replacement:** In the event of a verified claim, ShopEase ships a replacement unit prior to receiving your defective device.
- **Transferability:** ShopEase Care+ coverage is tied to the hardware serial number and automatically transfers if you gift or sell the product.

---

## 3. Customer Support Channels and Operating Hours

ShopEase provides multiple omnichannel support pathways designed to resolve inquiries rapidly:

| Support Channel | Availability / Hours | Target Response SLA | Best Suited For |
| :--- | :--- | :--- | :--- |
| **Live Chat (App & Web)** | 24 Hours / 7 Days a week | Under 60 seconds | Quick FAQs, order status, address adjustments |
| **Voice Support (1-800-555-EASE)** | Mon–Sat: 8:00 AM – 9:00 PM EST<br>Sun: 10:00 AM – 6:00 PM EST | Under 3 minutes hold | Complex returns, urgent delivery issues, payment authorization |
| **Email Support (support@shopease.com)** | 24 Hours / 7 Days a week | Within 4 hours | Detailed documentation, warranty claims, receipts |
| **Escalations Desk (priority@shopease.com)** | Mon–Fri: 9:00 AM – 5:00 PM EST | Within 24 hours | Disputed refunds, legal notices, safety reports |

---

## 4. Multi-Tier Support Escalation Framework

ShopEase utilizes a structured 3-tier escalation framework to ensure complex customer issues are diagnosed and resolved by specialized personnel:

```
[Customer Query]
       │
       ▼
[Tier 1 Support: Automated Chatbot / Frontline Specialist]
  • Answers FAQ policies, order tracking, address verification.
  • Resolution Target: 80% first-contact resolution within 5 minutes.
       │ (Unresolved / Low Confidence / Complex Claim)
       ▼
[Tier 2 Support: Senior Support Specialist]
  • Authority to authorize exceptions: up to $150 courtesy refunds, RMA overrides.
  • Performs remote technical diagnostics and returns inspection review.
  • Resolution Target: Within 12 business hours.
       │ (Systemic Hardware Flaw / Disputed Chargeback / Legal Issue)
       ▼
[Tier 3 Support: Customer Advocacy & Technical Engineering]
  • Lead Hardware Engineers, Logistics Managers, and Legal Counsel.
  • Full financial authority for complete replacements and formal damage settlements.
  • Direct phone consultation with dedicated case manager.
```

### Criteria for Escalating to a Human Agent / Tier 2:
1. **Low Confidence Score:** When the customer service AI system detects an inquiry confidence score below 0.70.
2. **Damaged Transit Claims:** Where customers provide photographic proof of physical courier crushing or broken items.
3. **Repeated Payment Decline:** Where error codes like `ERR_PAY_402` or `ERR_PAY_501` persist across two or more payment attempts.
4. **Safety & Hazard Warnings:** Any report involving battery swelling, smoke, electrical sparks, or skin irritation.
5. **Customer Frustration Detection:** Sentiment analysis triggering persistent negative emotion or explicit requests to "Speak with a human".

---

## 5. Filing a Formal Warranty Claim

To initiate a warranty repair or replacement claim:
1. Locate your 9-digit Order Number (e.g., #SE-8374921) and Product Serial Number (printed on box or device settings).
2. Email **warranty@shopease.com** with the subject line: `Warranty Claim: [Order Number] - [Product Name]`.
3. Provide a clear description of the defect and attach a short 10-second video demonstrating the malfunction.
4. Within 4 business hours, an agent will provide a prepaid courier return shipping label and a Warranty Service Ticket Number (WST-XXXXX).
5. Replacement units are dispatched within 2 business days of our service depot receiving the defective hardware.
"""

def main():
    print("Generating ShopEase sample documents in:", RAW_DATA_DIR)

    # 1. FAQ.md
    faq_path = RAW_DATA_DIR / "FAQ.md"
    with open(faq_path, "w", encoding="utf-8") as f:
        f.write(FAQ_MD_CONTENT.strip())
    print(f"Created: {faq_path.name} ({len(FAQ_MD_CONTENT.split())} words)")

    # 2. shipping_policy.txt
    shipping_path = RAW_DATA_DIR / "shipping_policy.txt"
    with open(shipping_path, "w", encoding="utf-8") as f:
        f.write(SHIPPING_POLICY_TXT_CONTENT.strip())
    print(f"Created: {shipping_path.name} ({len(SHIPPING_POLICY_TXT_CONTENT.split())} words)")

    # 3. return_policy.pdf (multi-page)
    return_pdf_path = RAW_DATA_DIR / "return_policy.pdf"
    generate_return_policy_pdf(return_pdf_path)
    print(f"Created: {return_pdf_path.name} (Multi-page PDF)")

    # 4. troubleshooting_guide.docx
    troubleshooting_path = RAW_DATA_DIR / "troubleshooting_guide.docx"
    generate_troubleshooting_guide_docx(troubleshooting_path)
    print(f"Created: {troubleshooting_path.name} (DOCX)")

    # 5. product_manual.pdf (multi-page)
    manual_pdf_path = RAW_DATA_DIR / "product_manual.pdf"
    generate_product_manual_pdf(manual_pdf_path)
    print(f"Created: {manual_pdf_path.name} (Multi-page PDF)")

    # 6. warranty_and_support.md
    warranty_path = RAW_DATA_DIR / "warranty_and_support.md"
    with open(warranty_path, "w", encoding="utf-8") as f:
        f.write(WARRANTY_AND_SUPPORT_MD_CONTENT.strip())
    print(f"Created: {warranty_path.name} ({len(WARRANTY_AND_SUPPORT_MD_CONTENT.split())} words)")

    print("\nAll 6 sample documents generated successfully in data/raw/")

if __name__ == "__main__":
    main()
