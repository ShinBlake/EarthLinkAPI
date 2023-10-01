import requests


token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjlhNTE5MDc0NmU5M2JhZTI0OWIyYWE3YzJhYTRlMzA2M2UzNDFlYzciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZWFydGhsaW5rcy03YzQ5MSIsImF1ZCI6ImVhcnRobGlua3MtN2M0OTEiLCJhdXRoX3RpbWUiOjE2OTYxNzc0OTAsInVzZXJfaWQiOiJzd2xmS09wa3V1UTRGQmc1ZmNHU3Fucmd2MzEyIiwic3ViIjoic3dsZktPcGt1dVE0RkJnNWZjR1NxbnJndjMxMiIsImlhdCI6MTY5NjE3NzQ5MCwiZXhwIjoxNjk2MTgxMDkwLCJlbWFpbCI6InNhbXBsZUBzYW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInNhbXBsZUBzYW1wbGUuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.LGhIMaQledbGbUEMG0Ls3n1c9Y_nJZyWOHDs1n72qA8Xm3ydtORPtHwAzgPD3-LhBsGf4P4btbKpPWRn2yrXYaoMzDcpqax1XGQM0xefflWScUHtZFIx24isuFCSZxri8-V8-W_ul_hkri2076iuMaTD7B9yxKbPKDMwMO8e8YWZetGh-a-gvDfq-HolsXRyaLSGhnQCdcMkW0PpTLaG_h5du4XsmZCgJH3H0DYWhSV4EZvDfpckNJcMBEMvmh7RyQWsIYWh2jyhPr06--u6seSNrEd0pTxxSoQ3cIh_vn6rRoRIXk45pZa-XbMhANsj3-zQKgv4bXIh_9nJdTeJWA"


def test_validate_endpoint():

    headers ={
        'authorization':token
    }

    response = requests.post(
        'http://127.0.0.1:8000/ping',
        headers = headers
    )

    return response.text




print(test_validate_endpoint())