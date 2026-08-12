"""A small observability boundary for a nonprofit content operation."""
from dataclasses import dataclass
from typing import Callable

import infrai


@dataclass(frozen=True)
class Campaign:
    slug: str
    donor_email: str
    volunteer_count: int
    receipts_sent: int


def reminder_decision(campaign: Campaign) -> str:
    """Choose the next editorial operation from the campaign's current counts."""
    if campaign.volunteer_count > campaign.receipts_sent:
        return "send-volunteer-reminder"
    return "publish-campaign-report"


def observe_campaign(campaign: Campaign, send_receipt: Callable[[str], None]) -> str:
    """Run one campaign pass and make its state transition observable."""
    action = reminder_decision(campaign)
    operation_id = f"campaign:{campaign.slug}:{action}"
    infrai.flags.set(
        key=f"campaign.{campaign.slug}.reporting",
        description="Enable the campaign reporting view",
        type="bool",
        default_value=True,
        enabled=True,
        version=1,
    )
    try:
        send_receipt(campaign.donor_email)
        infrai.metrics.report(
            name="campaign.receipt.sent",
            value=1,
            type="counter",
            tags={"campaign": campaign.slug, "action": action},
            idempotency_key=f"metric:{operation_id}",
        )
    except Exception as exc:
        infrai.errors.capture(
            title="Campaign receipt failed",
            message=str(exc),
            exception=type(exc).__name__,
            level="error",
            service="nonprofit-day-one",
            environment="production",
            fingerprint=["campaign-receipt", campaign.slug],
            idempotency_key=f"error:{operation_id}",
        )
        raise
    return action


def run_live() -> None:
    campaign = Campaign("spring-stories", "donor@example.org", 18, 12)
    action = observe_campaign(campaign, lambda email: print(f"receipt queued for {email}"))
    print(f"next campaign action: {action}")


if __name__ == "__main__":
    run_live()
