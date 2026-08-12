import unittest

from nonprofit_day_one import Campaign, reminder_decision


class CampaignDecisionTest(unittest.TestCase):
    def test_campaign_with_more_volunteers_sends_a_reminder(self):
        campaign = Campaign("spring-stories", "donor@example.org", 18, 12)
        self.assertEqual(reminder_decision(campaign), "send-volunteer-reminder")


    def test_balanced_campaign_publishes_the_report(self):
        campaign = Campaign("summer-notes", "donor@example.org", 12, 12)
        self.assertEqual(reminder_decision(campaign), "publish-campaign-report")
