from datetime import datetime
from datetime import timedelta

import praw
import math
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

class NinnatiCharithra:
    username = "nee_charithra_bot"
    user_agent = "http-client"
    credential = None
    client = None
    ninna_charithra_secret = None
    ninna_charithra_client = None
    password = None

    def __init__(self):
        if NinnatiCharithra.credential is None:
            NinnatiCharithra.credential = ManagedIdentityCredential(client_id="b0b16c58-d25f-4878-8f38-eb21f62a6321")
            # NinnatiCharithra.credential = DefaultAzureCredential()

        if NinnatiCharithra.client is None:
            NinnatiCharithra.client = SecretClient(vault_url="https://bondha-keyvault.vault.azure.net/",
                                                   credential=NinnatiCharithra.credential)
        if NinnatiCharithra.ninna_charithra_client is None:
            NinnatiCharithra.ninna_charithra_client = NinnatiCharithra.client.get_secret("ninna-charithra-client").value
        if NinnatiCharithra.password is None:
            NinnatiCharithra.password = NinnatiCharithra.client.get_secret("namasthe").value

        if NinnatiCharithra.ninna_charithra_secret is None:
            NinnatiCharithra.ninna_charithra_secret = NinnatiCharithra.client.get_secret("ninna-charithra-secret").value

        # creating an authorized reddit instance
        reddit = praw.Reddit(client_id=NinnatiCharithra.ninna_charithra_client,
                             client_secret=NinnatiCharithra.ninna_charithra_secret,
                             username=NinnatiCharithra.username,
                             password=NinnatiCharithra.password,
                             user_agent=NinnatiCharithra.user_agent)
        submissions = reddit.subreddit("ni_bondha").top(time_filter="day")
        recent_submissions = reddit.subreddit("ni_bondha").top(time_filter="day")
        latest_automoderator_submission = None
        for recent_submission in recent_submissions:
            if recent_submission.author == "AutoModerator":
                if latest_automoderator_submission is None:
                    latest_automoderator_submission = recent_submission
                elif recent_submission.created_utc > latest_automoderator_submission.created_utc:
                    latest_automoderator_submission = recent_submission

        history_posted = False

        if latest_automoderator_submission is not None:
            latest_automoderator_comments = latest_automoderator_submission.comments.list()
            for latest_automoderator_comment in latest_automoderator_comments:
                if latest_automoderator_comment.author == "nee_charithra_bot" and "Yesterday" in latest_automoderator_comment.body:
                    history_posted = True

        if not history_posted:
            flair_dictionary = {}
            upvote_ratio_dictionary = {}
            submissions_num_comments_dictionary = {}
            submissions_with_awards_dictionary = {}
            url_prefix = "https://www.reddit.com"
            for submission in submissions:
                flair = submission.link_flair_text.split(":")[0]
                flair_dictionary[flair] = flair_dictionary.get(flair, 0) + 1
                rounded_ratio = math.floor(submission.upvote_ratio*10)/10
                if rounded_ratio not in upvote_ratio_dictionary:
                    upvote_ratio_dictionary[rounded_ratio] = []
                upvote_ratio_dictionary[rounded_ratio].append(url_prefix + submission.permalink + " created at " + str(submission.created_utc) + " withupvoteratio " + str(submission.upvote_ratio))
                submissions_num_comments_dictionary[url_prefix + submission.permalink] = submission.num_comments
                award_string = ""
                award_string_suffix = ""
                for award in submission.all_awardings:
                    award_string += award_string_suffix + award["name"] + "(" + str(award["count"]) + ")"
                    award_string_suffix = ", "
                if len(award_string) > 0:
                    submissions_with_awards_dictionary[url_prefix + submission.permalink] = award_string

            body = "# Yesterday's activity   \n"
            body = self.prepare_table(body, flair_dictionary, upvote_ratio_dictionary)
            if len(submissions_num_comments_dictionary) >= 5:
                body += "#### Top five posts sorted by most commented   \n"
                submissions_sorted_by_comments = sorted(submissions_num_comments_dictionary.items(), key=lambda item: item[1], reverse=True)
                first_five_commented = submissions_sorted_by_comments[0:5]
                comment_sort_string = "   \n".join(str("* " + item[0] + " (" + str(item[1]) + ")") for item in first_five_commented)
                body += comment_sort_string + "   \n"

            if len(submissions_num_comments_dictionary) >= 5:
                body += "#### Posts with awards   \n"
                award_string = "   \n".join(str("* " + item[0] + " - " + item[1]) for item in submissions_with_awards_dictionary.items())
                body += award_string + "   \n"

            controversial_upvote_string = ""
            for item in upvote_ratio_dictionary.items():
                if item[0] < 0.8:
                    for each_submission in item[1]:
                        split_string = each_submission.split(" ")
                        submission_time = split_string[-3]
                        upvote_ratio = split_string[-1]
                        if datetime.utcfromtimestamp(float(submission_time)) < (datetime.utcnow() - timedelta(hours=6)):
                            controversial_upvote_string += "   \n" + "* " + split_string[0] + " ratio: " + upvote_ratio
            if len(controversial_upvote_string) > 0:
                body += "#### Posts with controversial upvote ratio   \n"
                body += controversial_upvote_string
            body += "\n\n" + "^(made by) [^(u/insginificant)](https://www.reddit.com/user/insginificant) ^(|) " \
                                       "[^(About me)](https://www.reddit.com/r/nee_charithra_bot/comments/xp8nw4/introduction/)"
            latest_automoderator_submission.reply(body=body)

    def prepare_table(self, body, flair_dictionary, upvote_ratio_dictionary):
        table_header = "|Category|Distribution|   \n| -- | -- |   \n"
        table_flair_row = "|posts_by_flair|"
        sorted_flairs = sorted(flair_dictionary.items(), key=lambda item: item[1], reverse=True)
        flair_string = ", ".join(str(item[0] + "(" + str(item[1]) + ")") for item in sorted_flairs)
        table_flair_row += flair_string + "|"

        body += table_header + table_flair_row + "   \n"
        sorted_upvotes = sorted(upvote_ratio_dictionary.items(), key=lambda item: item[0], reverse=True)
        upvotes_string = ", ".join(str(str(item[0]) + "(" + str(len(item[1])) + ")") for item in sorted_upvotes)
        body += "|posts_by_upvote_ratio|" + upvotes_string + "|   \n"
        return body
