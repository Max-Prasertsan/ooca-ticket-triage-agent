"""
Knowledge Base Mock Data
=========================

Contains mock knowledge base articles for demonstration purposes.

In production, this would be replaced with a real search backend
integration (Elasticsearch, Algolia, vector database, etc.).
"""

# Mock knowledge base articles
KNOWLEDGE_BASE_ARTICLES = [
    {
        "id": "KB-AUTH-001",
        "title": "How to Reset Your Password",
        "url": "https://help.example.com/articles/password-reset",
        "category": "authentication",
        "keywords": ["password", "reset", "forgot", "login", "access", "locked"],
        "content": """
        If you've forgotten your password or need to reset it, follow these steps:
        
        1. Go to the login page and click "Forgot Password"
        2. Enter your email address associated with your account
        3. Check your email for a password reset link (expires in 24 hours)
        4. Click the link and create a new password
        5. Your new password must be at least 12 characters with mixed case and numbers
        
        If you don't receive the email within 5 minutes, check your spam folder.
        Still having issues? Contact support for manual verification.
        """
    },
    {
        "id": "KB-AUTH-002",
        "title": "Two-Factor Authentication Setup Guide",
        "url": "https://help.example.com/articles/2fa-setup",
        "category": "authentication",
        "keywords": ["2fa", "two-factor", "authentication", "security", "mfa", "authenticator"],
        "content": """
        Two-factor authentication adds an extra layer of security to your account.
        
        To enable 2FA:
        1. Go to Settings > Security > Two-Factor Authentication
        2. Choose your preferred method (Authenticator App recommended)
        3. Scan the QR code with your authenticator app
        4. Enter the 6-digit code to verify
        5. Save your backup codes in a secure location
        
        Supported authenticator apps: Google Authenticator, Authy, 1Password.
        """
    },
    {
        "id": "KB-AUTH-003",
        "title": "Account Locked - Troubleshooting",
        "url": "https://help.example.com/articles/account-locked",
        "category": "authentication",
        "keywords": ["locked", "account", "blocked", "access", "denied", "suspended"],
        "content": """
        Your account may be locked for several reasons:
        
        - Too many failed login attempts (5 within 15 minutes)
        - Suspicious activity detected
        - Password expired (enterprise accounts)
        - Admin-initiated lock
        
        To unlock your account:
        1. Wait 15 minutes for automatic unlock (failed login attempts)
        2. Use the "Unlock Account" link in your email
        3. Contact support with your account ID for manual unlock
        
        For enterprise accounts, contact your organization administrator.
        """
    },
    {
        "id": "KB-BILLING-001",
        "title": "Understanding Your Billing Cycle",
        "url": "https://help.example.com/articles/billing-cycle",
        "category": "billing",
        "keywords": ["billing", "cycle", "payment", "invoice", "subscription", "charge", "renew"],
        "content": """
        Your billing cycle starts on the day you first subscribed or upgraded.
        
        Key billing information:
        - Pro plans are billed monthly on your subscription date
        - Enterprise plans are billed annually
        - Upgrades are prorated for the remaining billing period
        - Downgrades take effect at the next billing cycle
        
        View your billing history: Settings > Billing > Invoice History
        
        Payment methods: Credit card, PayPal, Wire transfer (Enterprise only)
        """
    },
    {
        "id": "KB-BILLING-002",
        "title": "How to Update Payment Information",
        "url": "https://help.example.com/articles/update-payment",
        "category": "billing",
        "keywords": ["payment", "credit card", "update", "billing", "method", "change"],
        "content": """
        To update your payment method:
        
        1. Go to Settings > Billing > Payment Methods
        2. Click "Add New Payment Method"
        3. Enter your card details
        4. Set as default payment method
        5. Optionally remove old payment methods
        
        Supported payment methods:
        - Visa, Mastercard, American Express
        - PayPal
        - Wire transfer (Enterprise only)
        
        Changes take effect immediately for future charges.
        """
    },
    {
        "id": "KB-BILLING-003",
        "title": "Requesting a Refund",
        "url": "https://help.example.com/articles/refund-policy",
        "category": "billing",
        "keywords": ["refund", "money back", "cancel", "dispute", "charge", "chargeback"],
        "content": """
        Our refund policy:
        
        - Full refund within 14 days of initial purchase
        - Prorated refund for annual plans cancelled mid-term
        - No refunds for monthly plans after the billing date
        
        To request a refund:
        1. Contact support with your account email
        2. Provide reason for refund request
        3. Allow 5-7 business days for processing
        
        Refunds are processed to the original payment method.
        """
    },
    {
        "id": "KB-OUTAGE-001",
        "title": "Service Status and Incident Response",
        "url": "https://help.example.com/articles/service-status",
        "category": "outage",
        "keywords": ["outage", "down", "status", "incident", "unavailable", "503", "error"],
        "content": """
        Check current service status: status.example.com
        
        During an outage:
        - We post updates every 15 minutes on our status page
        - Subscribe to status updates via email or SMS
        - Check @ExampleStatus on Twitter for real-time updates
        
        If you're experiencing issues not reflected on the status page:
        1. Clear your browser cache
        2. Try a different browser or incognito mode
        3. Check if the issue is region-specific
        4. Contact support if the issue persists
        
        SLA credits are automatically applied for qualifying outages.
        """
    },
    {
        "id": "KB-OUTAGE-002",
        "title": "Regional Connectivity Issues",
        "url": "https://help.example.com/articles/regional-issues",
        "category": "outage",
        "keywords": ["region", "latency", "slow", "connectivity", "network", "timeout"],
        "content": """
        If you're experiencing slow performance or connectivity issues:
        
        Check your region's status at status.example.com/regions
        
        Available regions:
        - us-east (Virginia)
        - us-west (Oregon)
        - eu-west (Ireland)
        - apac (Singapore)
        
        To switch regions:
        1. Go to Settings > Account > Region
        2. Select your preferred region
        3. Allow 5-10 minutes for propagation
        
        Contact support if issues persist after region change.
        """
    },
    {
        "id": "KB-API-001",
        "title": "API Rate Limits and Quotas",
        "url": "https://help.example.com/articles/api-rate-limits",
        "category": "api",
        "keywords": ["api", "rate limit", "quota", "429", "throttle", "exceeded"],
        "content": """
        API rate limits by plan:
        
        - Free: 100 requests/minute
        - Pro: 1,000 requests/minute
        - Enterprise: Custom limits (contact sales)
        
        When you exceed rate limits, you'll receive a 429 response.
        The response includes a Retry-After header.
        
        To request a rate limit increase:
        1. Contact support with your use case
        2. Provide expected request volume
        3. Enterprise customers can request custom limits
        
        Best practices: Implement exponential backoff and caching.
        """
    },
    {
        "id": "KB-FEATURE-001",
        "title": "Submitting Feature Requests",
        "url": "https://help.example.com/articles/feature-requests",
        "category": "product",
        "keywords": ["feature", "request", "suggestion", "idea", "roadmap", "feedback"],
        "content": """
        We love hearing your ideas! Here's how to submit feature requests:
        
        1. Visit our feedback portal: feedback.example.com
        2. Search for existing requests (and upvote if found)
        3. Click "New Idea" to submit a new request
        4. Provide a clear description and use case
        
        Our product team reviews all submissions weekly.
        Popular requests are added to our public roadmap.
        
        You'll receive updates when your request status changes.
        """
    },
    {
        "id": "KB-ACCOUNT-001",
        "title": "Managing Team Members",
        "url": "https://help.example.com/articles/team-management",
        "category": "account",
        "keywords": ["team", "member", "invite", "user", "admin", "permission", "role"],
        "content": """
        To manage your team (Pro and Enterprise plans):
        
        Adding members:
        1. Go to Settings > Team > Members
        2. Click "Invite Member"
        3. Enter email and select role
        4. Member receives invitation email
        
        Roles and permissions:
        - Viewer: Read-only access
        - Editor: Create and edit content
        - Admin: Full access including billing
        - Owner: Cannot be removed, can transfer ownership
        
        Enterprise plans have custom role creation available.
        """
    },
    {
        "id": "KB-ACCOUNT-002",
        "title": "Canceling Your Subscription",
        "url": "https://help.example.com/articles/cancel-subscription",
        "category": "account",
        "keywords": ["cancel", "subscription", "close", "delete", "account", "end"],
        "content": """
        To cancel your subscription:
        
        1. Go to Settings > Billing > Subscription
        2. Click "Cancel Subscription"
        3. Select your reason (helps us improve)
        4. Confirm cancellation
        
        What happens after cancellation:
        - Access continues until end of billing period
        - Data retained for 30 days after expiration
        - You can reactivate anytime within 30 days
        - After 30 days, data is permanently deleted
        
        Enterprise contracts: Contact your account manager.
        """
    },
    {
        "id": "KB-UI-001",
        "title": "Dashboard Customization Options",
        "url": "https://help.example.com/articles/dashboard-customization",
        "category": "product",
        "keywords": ["dashboard", "customize", "theme", "dark mode", "layout", "display"],
        "content": """
        Customize your dashboard experience:
        
        Theme options:
        - Light mode (default)
        - Dark mode (coming soon!)
        - System preference sync
        
        Layout customization:
        1. Go to Settings > Display > Layout
        2. Drag and drop widgets
        3. Resize panels as needed
        4. Save as default layout
        
        Accessibility options available in Settings > Accessibility.
        We're actively working on additional theme options.
        """
    },
]