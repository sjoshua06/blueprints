import json
import urllib.parse
import urllib.request

SUPABASE_URL = "https://qwzicqpyogewrbjdakin.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3emljcXB5b2dld3JiamRha2luIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzU0NjI5MSwiZXhwIjoyMDg5MTIyMjkxfQ.8-puPQiZuViihx2E_sEgyM0VlRdNLWRFndpCljjvWh4"  # ← get from Supabase Dashboard → Settings → API

class SimpleSupabase:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def table(self, table_name):
        return TableQuery(self.url, self.headers, table_name)

class TableQuery:
    def __init__(self, url, headers, table_name):
        self.url      = url
        self.headers  = headers
        self.table    = table_name
        self.filters  = {}
        self._cols    = "*"
        self._order   = None
        self._upsert  = None

    def select(self, cols="*"):
        self._cols = cols
        return self

    def eq(self, col, val):
        self.filters[col] = f"eq.{val}"
        return self

    def order(self, col, desc=False):
        self._order = f"{col}.{'desc' if desc else 'asc'}"
        return self

    def upsert(self, data):
        self._upsert = data
        return self

    def delete(self):
        self._delete = True
        return self

    def execute(self):
        if hasattr(self, '_delete') and self._delete:
            params = {}
            params.update(self.filters)
            query = urllib.parse.urlencode(params)
            url   = f"{self.url}/rest/v1/{self.table}?{query}"
            req   = urllib.request.Request(url, headers=self.headers, method="DELETE")
            try:
                with urllib.request.urlopen(req) as r:
                    data = json.loads(r.read()) if r.length else []
            except urllib.error.HTTPError as e:
                pass
            return type("R", (), {"data": []})()
        elif self._upsert is not None:
            url     = f"{self.url}/rest/v1/{self.table}"
            payload = json.dumps(self._upsert).encode("utf-8")
            headers = {
                **self.headers,
                "Prefer": "resolution=merge-duplicates",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req) as r:
                body = r.read()
                data = json.loads(body) if body else []
            return type("R", (), {"data": data})()
        else:
            params = {"select": self._cols}
            params.update(self.filters)
            if self._order:
                params["order"] = self._order
            query = urllib.parse.urlencode(params)
            url   = f"{self.url}/rest/v1/{self.table}?{query}"
            req   = urllib.request.Request(url, headers=self.headers, method="GET")
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            return type("R", (), {"data": data})()
supabase = SimpleSupabase(SUPABASE_URL, SUPABASE_KEY)

# Official client for Storage operations
from supabase import create_client, Client
official_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)