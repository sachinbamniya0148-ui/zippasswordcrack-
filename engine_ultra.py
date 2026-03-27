#!/usr/bin/env python3
"""engine_ultra.py v23 — Parallel Batch Speed Engine — ZipPasswordCrack.in
Real genuine speed: 10k-50k/s standard ZIP, ~500/s AES-256 (hardware limit).
Uses ThreadPoolExecutor for parallel batch cracking — genuine multi-threaded.
"""
import itertools, string, logging, time, zipfile, re, tempfile, shutil, os, threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED

log = logging.getLogger("engine")

try:
    import pyzipper; HAS_AES = True
except:
    HAS_AES = False

try:
    import pikepdf; HAS_PIKE = True
except:
    HAS_PIKE = False

try:
    from pypdf import PdfReader as _PDF; HAS_PDF = True
except:
    try:
        from PyPDF2 import PdfReader as _PDF; HAS_PDF = True
    except:
        HAS_PDF = False

# ─── Character Sets ──────────────────────────────────────────────────────────
CS = {
    "lower":    string.ascii_lowercase,
    "upper":    string.ascii_uppercase,
    "digits":   string.digits,
    "alpha":    string.ascii_letters,
    "alnum":    string.ascii_letters + string.digits,
    "sym":      "!@#$%^&*()-_+=[]{}|;:',.<>?/`~\\",
    "sym_india": "!@#$%&*_-.+~",
    "hex":      "0123456789abcdef",
    "full":     string.printable.strip(),
}

# Common emoji used in passwords (rare but real)
EMOJI_PASSWORDS = [
    "❤️123", "🔥786", "💯100", "🙏786", "😊123", "👑786", "🌟123", "💪786",
    "🎯123", "🚀786", "💎123", "👍786", "🌈123", "🦁786", "⚡123", "🎉786",
]

# ─── Word Banks ───────────────────────────────────────────────────────────────
TOP_COMMON = [
    "123456","password","123456789","12345678","12345","qwerty","abc123","password1",
    "admin","letmein","welcome","monkey","dragon","master","sunshine","princess",
    "iloveyou","111111","000000","password123","admin123","root","toor","pass","test",
    "guest","1234","1234567","1234567890","qwertyuiop","asdfghjkl","qwerty123","1q2w3e4r",
    "zaq1xsw2","p@ssw0rd","P@ssword","pa55word","pa$$word","admin@123","Admin@123",
    "Admin123","user123","test123","demo123","india","bharat","india123","bharat123",
    "india786","bharat786","india2024","786","786786","007","007007","420","420420",
    "108","108108","999","9999","pakistan","pakistan123","lahore","karachi","islamabad",
    "bangladesh","dhaka","pass@123","Pass@123","P@ss123","1qaz2wsx","!QAZ2wsx","zxcvbn",
    "q1w2e3r4","a1s2d3f4","abcd1234","1234abcd","abc@123","ABC123","Abc@123",
    "letmein123","master123","batman","superman","pokemon","samsung","iphone","android",
    "windows","google","facebook","instagram","whatsapp","cricket","dhoni","kohli",
    "sachin","rohit","virat","msdhoni","bollywood","shahrukh","salman","aamir","hrithik",
    "deepika","katrina","rahul","priya","pooja","neha","anjali","sunny","lucky","rocky",
    "sharma","verma","gupta","kumar","singh","patel","mumbai","delhi",
    "maa","baap","papa","bhai","didi","dost","yaar","786@123","@786",
    "qwerty1","password2","123456a","a123456","football","baseball","soccer",
    "love","loveyou","iloveu","hello","hello123","secret","secret1","god","lord",
    "allah786","michael","jessica","daniel","jordan","harley",
    "1234pass","pass1234","mypassword","mypass","changeme","change123",
    "letmein1","welcome1","admin1234","administrator","superuser","superadmin",
    "root123","rootpass","system","system123","default","default123",
    "123","1234","12345","password!","pass123","abc","abcd","1111","2222","3333",
    "4444","5555","6666","7777","8888","9999","0000","11111","22222","33333",
    "12341234","pass@1234","Password@1","Admin@1234","welcome123","Welcome@123",
    "Test@1234","User@1234","login","Login123","login123","qazwsx","edcrfv",
    "tgbyhn","ikmnbv","plmnko","1029384756","2580","258025","147","1478","1470",
    "159","1596","7894","4561","7415","8520","9630","2143","6589","0987654321",
    # India-specific
    "bharat2024","india@2024","jai@hind","vandemataram","jai786","786jai","om786",
    "krishna786","ram786","shiv786","ganesh786","allah786","waheguru786",
    "1947india","india1947","bharat1947","swatantrata","independence",
    # More common
    "abc@1234","Abc1234","abc1234@","@abc1234","1234@abc","Password1!",
    "password@1","pass@word1","india@123","India@123","INDIA123","india2025",
]

YEARS = [str(y) for y in range(1940, 2026)]
NUMS = ["1","2","3","12","21","123","321","1234","12345","123456","786","007","420","108",
        "999","2024","2025","1947","00","01","02","11","22","33","99","2000","2001","786786",
        "7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23",
        "24","25","1","2","3","4","5","6","7","8","9","100","200","300","400","500"]

SYM_NUMS = ["@123","@1234","!123","#123","@786","@007","_123","_786","@2024","@2025","@india",
            "!@#","@1","!1","#1","_1","_12","_2024","@786786","#786","@123456","!1234","@12345",
            "@2023","@2022","#2024","!2024","_2024","@000","@111","@786786","#123456"]

SUFS = (["","1","2","3","12","21","123","321","1234","4321","12345","54321","123456","654321",
         "1234567","12345678","123456789","1234567890","@","@1","@12","@123","@1234","@12345",
         "@786","@007","@420","@108","#","#123","!","!123","_","_123","_786","_007","0","00",
         "000","0000","786","786786","007","007007","420","108","999","9999",
         "@2024","@2025","@india","ji","_ji","bhai","india","kumar",
         "2024","2025","2023","2022","@2023","@2022","@2021","@2020",
         "jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec",
         "@jan","@feb","@mar","@apr","@may","@jun","@jul","@aug","@sep","@oct","@nov","@dec",
         "1996","1997","1998","1999","2000","2001","2002","2003","2004","2005",
         "@1996","@1997","@1998","@1999","@2000","@2001","@2002","@2003",
         ] + SYM_NUMS)

PRES = ["","my","the","new","old","its","real","true","shri","dr","mr","mrs","786","007","@","#","1","i","we","our","new"]

DATE_FMTS = ["%d%m%Y","%d%m%y","%Y%m%d","%d/%m/%Y","%d-%m-%Y","%d.%m.%Y","%m%d%Y",
             "%Y%d%m","%d%m","%m%Y","%Y","%d","%m","%d%b%Y","%b%Y","%B%Y",
             "%Y-%m-%d","%y%m%d","%m/%d/%Y","%d%b%y","%b%d%Y","%d%b","%b%d"]

INDIAN_NAMES = [
    "rahul","amit","sunil","anil","ravi","sanjay","vijay","ajay","raj","ram","krishna",
    "shyam","mohan","rohan","karan","arjun","vikram","suresh","mahesh","ganesh","dinesh","rajesh",
    "mukesh","deepak","pradeep","sandeep","kuldeep","pankaj","vivek","abhishek","manish","ankit",
    "mohit","rohit","sumit","lalit","nikhil","sahil","tushar","gaurav","sourav","anurag","mayank",
    "neeraj","dheeraj","kunal","vishal","vaibhav","saurabh","himanshu","shubham","akash","prakash",
    "aditya","harsh","yash","sunny","lucky","bobby","rocky","pappu","guddu","bunty","bablu","pintu",
    "rinku","raju","raja","sonu","monu","harpreet","gurpreet","manpreet","balwinder","amarjit",
    "gurjit","ranjit","imran","asif","zaid","farhan","ayaan","danish","faizan","rizwan","bilal",
    "usman","hassan","ali","amir","salman","sultan","shahid","khalid","rashid","mohd","mohammed",
    "muhammad","ahmad","ahmed","iqbal","nawaz","asad","babar","murugan","karthik","senthil",
    "anand","prasad","priya","pooja","neha","rita","geeta","sita","meena","seema","reena","sunita",
    "kavita","lalita","rekha","meera","sheela","kamla","vimla","sharmila","shweta","nisha","disha",
    "asha","usha","radha","divya","kavya","riya","tara","anjali","mamta","deepika","shreya",
    "sweety","pinky","simran","ayesha","fatima","zainab","maryam","khadija","zahra","asma",
    "noor","sana","hina","mehak","mehwish","amna","bushra","farida","nasreen","parveen",
    "sachin","virat","dhoni","kohli","tendulkar","rohit","bumrah","jadeja","shami","pandya",
    "harbhajan","yuraj","zaheer","sehwag","gambhir","dravid","laxman","ganguly","kumble",
    # More names
    "ratan","naresh","sudhir","surendra","mahendra","rajendra","narendra","virendra","devendra",
    "jitendra","yogendra","ravindra","harendra","shailendra","lokendra","nripendra",
    "poonam","ritu","preeti","jyoti","manju","geeta","nisha","usha","asha","lata","gita",
    "radha","sushma","rama","savita","sudha","varsha","meenu","baby","sweetu","dolly",
    "sukhwinder","lakhwinder","jaswinder","kulwinder","rajwinder","pravinder","bhupinder",
    "tariq","waseem","nadeem","naseem","saleem","raheem","hakeem","naeem","azeem","kareem",
    # South Indian names
    "venkat","raman","subramaniam","krishnamurthy","narasimhan","ramakrishna","srinivasan",
    "balakrishnan","raghunathan","subramanian","venkataramaiah","narayanasamy",
    "arumugam","karuppasamy","murugesan","selvam","tamilarasan","velayutham","manikandan",
]

SURNAMES = [
    "sharma","verma","gupta","kumar","singh","patel","shah","mehta","joshi","tiwari",
    "pandey","mishra","yadav","chauhan","rajput","thakur","rao","reddy","naidu","nair","pillai",
    "iyer","menon","banerjee","chatterjee","mukherjee","ghosh","das","bose","roy","saha","mitra",
    "basu","chowdhury","khan","ansari","qureshi","shaikh","sheikh","siddiqui","malik","mirza",
    "gill","dhillon","sandhu","grewal","sidhu","kang","brar","agarwal","goyal","mittal","goel",
    "jain","kapoor","khanna","chopra","malhotra","arora","kohli","shukla","dubey","tripathi",
    "upadhyay","bamniya","solanki","rawat","bisht","negi","bhandari","rana","maurya","bajpai",
    "srivastava","awasthi","saxena","tyagi","garg","bansal","bhatt","dixit","trivedi",
    "chaudhary","rathore","sisodiya","bundela","chandel","gahlot","sisodia","naruka","gehlot",
    "dalit","meena","gurjar","jat","ahir","lohar","kumhar","nai","kumbhar","goud",
]

CITIES = [
    "mumbai","delhi","bangalore","bengaluru","chennai","kolkata","hyderabad","pune",
    "ahmedabad","jaipur","surat","lucknow","kanpur","nagpur","indore","bhopal","patna","vadodara",
    "agra","nashik","faridabad","meerut","rajkot","amritsar","varanasi","prayagraj","jodhpur",
    "guwahati","kochi","chandigarh","noida","gurgaon","thane","ranchi","lahore","karachi",
    "islamabad","rawalpindi","peshawar","dhaka","chittagong","sylhet","dubai","abudhabi","riyadh",
    "kolkata","vizag","coimbatore","madurai","tiruchirappalli","bhilai","raipur","gwalior",
    "allahabad","jabalpur","srinagar","aurangabad","solapur","hubli","dharwad","bareilly",
    "moradabad","ghaziabad","noida","gurugram","faridabad","rohtak","panipat","sonipat",
    "hisar","karnal","ambala","yamunanagar","kurukshetra","sirsa","rewari","palwal",
]

HINDI = [
    "pyar","mohabbat","ishq","prem","preet","sneh","mamta","dard","khushi","gham","dukh",
    "sukh","aanand","shanti","umeed","aasha","sapna","khwaab","armaan","dil","zindagi","jeevan",
    "duniya","maa","baap","papa","baba","amma","ammi","abbu","dadi","dada","nani","nana","bhai",
    "bhaiya","didi","behan","beta","beti","baccha","parivaar","ghar","ram","krishna","shiva",
    "ganesh","allah","waheguru","sona","mona","gudiya","munni","rani","raja","dost","yaar",
    "sahab","ji","cricket","dhoni","kohli","sachin","rohit","virat","ipl","t20","bollywood",
    "shahrukh","salman","deepika","katrina","priyanka","anushka","india","bharat","hindustan",
    "786","007","420","108","999","1947","jai","hind","vande","mataram","bhagwan","ishwar",
    "zindabad","aman","chain","barkat","dua","nazar","hifazat","mehnat","kamyabi","khuda",
    "bismillah","mashallah","inshallah","alhamdulillah","subhanallah","jazakallah",
]

MOBILE_CC = {
    "+91":  {"px": ["6","7","8","9","70","71","72","73","74","75","76","77","78","79",
                    "80","81","82","83","84","85","86","87","88","89","90","91","92","93","94","95","96","97","98","99"], "tlen": 10},
    "+92":  {"px": ["30","31","32","33","34","300","301","310","320","321","330","331"], "tlen": 10},
    "+880": {"px": ["13","14","15","16","17","18","19","130","140","150","170","180"], "tlen": 10},
    "+1":   {"px": ["201","202","212","213","310","312","408","415","469","646","702","917"], "tlen": 10},
    "+44":  {"px": ["7400","7500","7600","7700","7800","7900"], "tlen": 10},
    "+86":  {"px": ["130","131","132","135","136","137","138","150","151","158","180","181"], "tlen": 11},
    "+971": {"px": ["50","52","54","55","56","58"], "tlen": 9},
    "+966": {"px": ["50","53","54","55","56","57","58","59"], "tlen": 9},
    "+62":  {"px": ["81","82","83","85","87","89","811","812","821","852"], "tlen": 10},
    "+55":  {"px": ["11","21","31","41","51","61","71","81","91"], "tlen": 11},
    "+7":   {"px": ["900","901","903","905","910","911","912","916","917"], "tlen": 10},
    "+49":  {"px": ["151","152","157","159","160","162","163","170","171","172"], "tlen": 11},
    "+33":  {"px": ["60","61","62","63","64","65","66","67","68","69"], "tlen": 9},
    "+81":  {"px": ["70","80","90"], "tlen": 10},
    "+82":  {"px": ["10","11","16","17","18","19"], "tlen": 10},
    "+234": {"px": ["70","80","81","90","803","806","810","813"], "tlen": 10},
    "+20":  {"px": ["10","11","12","15","19"], "tlen": 10},
    "+27":  {"px": ["60","61","71","72","73","74","76","78","79","81","82","83"], "tlen": 9},
}

GITHUB_LISTS = {
    "top1m":    "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
    "top100k":  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt",
    "top10k":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
    "best1050": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/best1050.txt",
    "xato1m":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/xato-net-10-million-passwords-1000000.txt",
    "probable": "https://raw.githubusercontent.com/berzerk0/Probable-Wordlists/master/Real-Passwords/Top12Thousand-probable-v2.txt",
    "weakpass": "https://raw.githubusercontent.com/kkrypt0nn/wordlists/main/wordlists/passwords/common_passwords_win.txt",
    "leaked":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/alleged-gmail-passwords.txt",
    "rockyou":  "https://raw.githubusercontent.com/brannondorsey/naive-hashcat/master/rockyou.txt",
    "common_3k":"https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/common-passwords-win.txt",
    "bt4":      "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/bt4-password.txt",
    "darkweb":  "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/darkweb2017-top10000.txt",
    "top500":   "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/500-worst-passwords.txt",
    "hak5":     "https://raw.githubusercontent.com/nicowillis/passwords/master/common_10000_passwords.txt",
    "kaonashi": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/Ashley-Madison.txt",
}

# ─── Helper Functions ─────────────────────────────────────────────────────────
def _ok(pw): return bool(pw and isinstance(pw, str) and 3 <= len(pw) <= 128)

LEET = [
    {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7', 'b': '8', 'g': '9', 'l': '1'},
    {'a': '4', 'e': '3', 'i': '!', 'o': '0', 's': '5', 't': '7', 'b': '6', 'g': '9'},
]

def leet(w):
    r = set()
    for m in LEET:
        v = w.lower()
        for k, val in m.items():
            v = v.replace(k, val)
        if v != w.lower() and _ok(v):
            r.add(v)
    return list(r)

def rules(word):
    if not word: return []
    w = word.lower(); wc = word.capitalize(); wu = word.upper(); wr = word[::-1]
    return list(set(r for r in [w, wc, wu, wr, wr.capitalize()] + leet(w) if _ok(r)))

def interleave(word, num):
    results = []
    w = word[:8]; n = str(num)[:8]
    r = "".join(a + b for a, b in zip(w, n.ljust(len(w), '0')))
    if _ok(r): results.append(r)
    for i in range(0, len(w) + 1, 2):
        pw = w[:i] + n + w[i:]
        if _ok(pw): results.append(pw)
    return results

def google_style(words):
    for word in words:
        w = word.lower(); wc = word.capitalize(); wu = word.upper()
        for yr in YEARS:
            yield w + yr; yield wc + yr; yield wu + yr
            yield w + "@" + yr; yield wc + "@" + yr
            yield yr + w; yield yr + wc
        for n in NUMS:
            yield w + n; yield wc + n; yield wu + n
            yield n + w; yield n + wc
        for sym in ["@", "!", "#", "_"]:
            for n in ["1", "12", "123", "786", "2024", "2025", "007", "420"]:
                yield w + sym + n; yield wc + sym + n
        for n in ["786", "007", "420", "108", "2024", "2025", "1947", "999", "123456", "12345"]:
            for sep in ["", "@", "#", "_", "."]:
                yield w + sep + n; yield wc + sep + n; yield wu + n
        if len(w) <= 6:
            yield w + w; yield wc + w; yield w + wc
        for r in leet(w):
            yield r; yield r.capitalize()

# ─── Generators ──────────────────────────────────────────────────────────────
def gen_top_common():
    seen = set()
    for pw in TOP_COMMON:
        for v in [pw, pw.upper(), pw.capitalize(), pw.lower()]:
            if _ok(v) and v not in seen:
                seen.add(v); yield v
        for s in ["1", "12", "123", "@", "!", "786", "@123", "@2024", "@2025", "",
                  "2024", "2025", "#123", "!@#", "_123", "_786", "@007", "@420"]:
            pw2 = pw + s
            if _ok(pw2) and pw2 not in seen:
                seen.add(pw2); yield pw2


def gen_google_common():
    words = (TOP_COMMON[:80] + INDIAN_NAMES[:100] + HINDI[:80] + CITIES[:40])
    seen = set()
    for pw in google_style(words):
        if _ok(pw) and pw not in seen:
            seen.add(pw); yield pw


def gen_smart(info):
    name  = (info.get("name")  or "").strip()
    dob   = (info.get("dob")   or "").strip()
    mobile= (info.get("mobile")or "").strip()
    city  = (info.get("city")  or "").strip()
    nick  = (info.get("nick")  or "").strip()
    pet   = (info.get("pet")   or "").strip()
    fav   = (info.get("fav")   or "").strip()
    lucky = (info.get("lucky") or "").strip()
    other = (info.get("other") or "").strip()

    dt_obj = None
    if dob:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d",
                    "%d%m%Y", "%d%m%y", "%Y%m%d", "%d/%m/%y"):
            try:
                dt_obj = datetime.strptime(dob.strip(), fmt); break
            except:
                pass

    date_strs = []
    if dt_obj:
        for fmt in DATE_FMTS:
            try:
                ds = dt_obj.strftime(fmt)
                if ds not in date_strs:
                    date_strs.append(ds)
            except:
                pass

    tokens = [t for t in [name, nick, pet, fav, city, other] if t]
    lucky_nums = [lucky] if lucky else []
    lucky_nums += ["786", "007", "420", "108", "999", "123", "1234", "2024", "2025", "1947"]
    if dt_obj:
        lucky_nums += [
            str(dt_obj.year),
            f"{dt_obj.day:02d}{dt_obj.month:02d}",
            f"{dt_obj.month:02d}{dt_obj.day:02d}",
            str(dt_obj.year)[-2:],
            f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}",
        ]

    # Google-style combos
    for pw in google_style(tokens):
        yield pw

    # Prefix+word+suffix
    for tok in tokens:
        for v in rules(tok):
            for s in SUFS:
                for p in PRES:
                    pw = p + v + s
                    if _ok(pw):
                        yield pw

    # Interleaved combos
    for tok in tokens:
        for num in lucky_nums:
            for pw in interleave(tok.lower(), num):
                yield pw
            for pw in interleave(tok.capitalize(), num):
                yield pw

    # Token + date combos
    for tok in tokens:
        for ds in date_strs:
            for sep in ["", "_", "-", ".", "@", "#", "/"]:
                for v in [tok.lower(), tok.capitalize(), tok.upper()]:
                    for combo in [v + sep + ds, ds + sep + v, v + ds, ds + v]:
                        if _ok(combo):
                            yield combo

    # DOB + name combos (very common Indian pattern)
    if dt_obj and tokens:
        for tok in tokens:
            for v in [tok.lower(), tok.capitalize()]:
                dob_patterns = [
                    f"{dt_obj.day:02d}{dt_obj.month:02d}",
                    f"{dt_obj.day:02d}{dt_obj.month:02d}{dt_obj.year}",
                    f"{dt_obj.day:02d}{dt_obj.month:02d}{str(dt_obj.year)[-2:]}",
                    f"{dt_obj.year}{dt_obj.month:02d}{dt_obj.day:02d}",
                    f"{dt_obj.month:02d}{dt_obj.year}",
                    str(dt_obj.year),
                ]
                for dob_p in dob_patterns:
                    for sep in ["", "@", "_", "-", "#", "."]:
                        for combo in [v + sep + dob_p, dob_p + sep + v]:
                            if _ok(combo):
                                yield combo

    # Mobile combos
    if mobile:
        m = re.sub(r'[\s\-\+\(\)]', '', mobile)
        for v in [mobile, m, m[-10:], m[-8:], m[-6:], m[-4:], "0" + m[-10:], "91" + m[-10:]]:
            if v and _ok(v):
                yield v
            for s in SUFS[:30]:
                pw = v + s
                if _ok(pw):
                    yield pw
        for tok in tokens:
            for v in [tok.lower(), tok.capitalize()]:
                for vm in [m[-10:], m[-8:], m[-6:], m[-4:]]:
                    for combo in [v + vm, vm + v, v + "_" + vm, v + "@" + vm]:
                        if _ok(combo):
                            yield combo

    # Lucky number combos
    if lucky:
        for tok in tokens:
            for v in rules(tok):
                for sep in ["", "@", "#", "_", "."]:
                    for combo in [v + sep + lucky, lucky + sep + v]:
                        if _ok(combo):
                            yield combo

    # Date-only combos
    for ds in date_strs:
        for s in SUFS[:30]:
            for p in PRES[:12]:
                pw = p + ds + s
                if _ok(pw):
                    yield pw

    # Multi-token combos
    if len(tokens) >= 2:
        for r in range(2, min(len(tokens) + 1, 5)):
            for perm in itertools.permutations(tokens[:6], r):
                for sep in ["", "_", "-", "@", "."]:
                    pw = sep.join(p.lower() for p in perm)
                    if _ok(pw): yield pw
                    pw = sep.join(p.capitalize() for p in perm)
                    if _ok(pw): yield pw
    if len(tokens) >= 2:
        for t1 in tokens:
            for t2 in tokens:
                if t1 == t2: continue
                for num in lucky_nums[:10]:
                    for combo in [
                        t1.lower() + num + t2.lower(),
                        t1.capitalize() + num + t2.capitalize(),
                        t1.lower() + t2.lower() + num,
                    ]:
                        if _ok(combo): yield combo


def gen_calendar(start=1940, end=2025, prefixes=None, suffixes=None, fmts=None, seps=None):
    prefixes = prefixes or [""]
    suffixes = suffixes or [""]
    seps     = seps or ["", "_", "-", ".", "@", "#", "/"]
    fmts     = fmts or DATE_FMTS
    for year in range(start, end + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day)
                except:
                    continue
                dstrs = []
                for fmt in fmts:
                    try:
                        ds = dt.strftime(fmt)
                        if ds not in dstrs: dstrs.append(ds)
                    except:
                        pass
                for ds in dstrs:
                    for pre in prefixes:
                        for suf in suffixes:
                            for sep in seps:
                                if pre and suf:
                                    combos = [pre + sep + ds + sep + suf, pre + ds + suf]
                                elif pre:
                                    combos = [pre + sep + ds, pre + ds]
                                elif suf:
                                    combos = [ds + sep + suf, ds + suf]
                                else:
                                    combos = [ds]
                                for pw in combos:
                                    for v in [pw, pw.upper(), pw.capitalize()]:
                                        if _ok(v): yield v


def gen_keyboard():
    WALKS = [
        "qwerty","qwerty123","qwerty@123","Qwerty123","QWERTY","QWERTY123",
        "asdf","asdf123","asdf@123","Asdf123","asdfghjkl","1qaz","1qaz2wsx",
        "!qaz2wsx","1Qaz2Wsx","!QAZ2wsx","zxcvbn","qazwsx","qazwsx123",
        "1q2w3e","1q2w3e4r","1Q2W3E4R","q1w2e3","q1w2e3r4","Q1W2E3R4",
        "abcd1234","1234abcd","abc@123","ABC123","qweasdzxc","qweasd",
        "12qwaszx","zxcasqw12","pl,","poiuytrewq","mnbvcxz",
    ]
    rows = [
        "qwertyuiop","asdfghjkl","zxcvbnm","1234567890","QWERTYUIOP",
        "q1w2e3r4","1q2w3e4r","a1s2d3f4","z1x2c3v4","123456789","987654321",
        "246810","135790","159753","963741","147258369","369258147",
    ]
    seen = set()
    for walk in WALKS:
        for suf in ["", "1", "123", "@123", "!", "@", "786", "@786", "@2024", "@2025", "2024"]:
            pw = walk + suf
            if _ok(pw) and pw not in seen:
                seen.add(pw); yield pw
    for row in rows:
        for start in range(len(row)):
            for ln in range(2, min(len(row) + 1, 16)):
                seg = row[start:start + ln]
                if len(seg) < ln: break
                rev = seg[::-1]
                for base in [seg, rev]:
                    for suf in ["", "1", "12", "123", "1234", "!", "@", "@123", "786", "007"]:
                        for pre in ["", "1", "123", "786", "@"]:
                            pw = pre + base + suf
                            if _ok(pw) and pw not in seen:
                                seen.add(pw); yield pw


def gen_dict_streaming(paths):
    import urllib.request
    for p in (paths or []):
        p = str(p).strip()
        if not p: continue
        if p.startswith("http://") or p.startswith("https://"):
            log.info("Streaming: " + p)
            try:
                req = urllib.request.Request(p, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    for raw in resp:
                        try:
                            pw = raw.decode("utf-8", "ignore").strip()
                            if not _ok(pw): continue
                            yield pw
                            wl = pw.lower()
                            if _ok(wl) and wl != pw: yield wl
                            wc = pw.capitalize()
                            if _ok(wc) and wc != pw: yield wc
                            # Mutations
                            yield pw + "1"; yield pw + "123"
                            yield pw + "@123"; yield pw + "786"
                        except:
                            pass
            except Exception as e:
                log.warning("URL: " + str(e))
            continue
        fp = Path(p)
        if not fp.exists(): continue
        try:
            with open(fp, "r", errors="ignore", encoding="utf-8") as f:
                for line in f:
                    pw = line.strip()
                    if _ok(pw): yield pw
        except:
            pass


def gen_indian_wordlist():
    all_words = HINDI + INDIAN_NAMES[:200] + SURNAMES[:120] + CITIES[:100]
    seen = set()
    for word in all_words:
        for v in rules(word):
            for s in SUFS:
                for p in PRES:
                    pw = p + v + s
                    if _ok(pw) and pw not in seen:
                        seen.add(pw); yield pw


def gen_mobile(numbers=None, country_codes=None, extras=None, density=100):
    if numbers:
        for num in numbers:
            num = re.sub(r'[\s\-\+\(\)]', '', num)
            if not num.isdigit() or len(num) < 4: continue
            for v in [num, num[-10:], num[-8:], num[-6:], num[-4:],
                      "0" + num[-10:], "91" + num[-10:]]:
                if v and _ok(v): yield v
                for s in SUFS[:25]:
                    pw = v + s
                    if _ok(pw): yield pw
    codes = country_codes or ["+91"]
    exps  = extras or []
    for cc in codes:
        info = MOBILE_CC.get(cc)
        if not info: continue
        pfx_list = info["px"] + exps
        tlen = info["tlen"]
        for pfx in pfx_list:
            tail_len = tlen - len(pfx)
            if tail_len < 0: continue
            total = 10 ** tail_len
            step = max(1, int(total * (100 - min(density, 100)) / 10000)) if density < 100 else 1
            for n in range(0, total, step):
                tail = str(n).zfill(tail_len)
                full = pfx + tail
                for v in [full, "0" + full, cc.lstrip("+") + full]:
                    if v and _ok(v): yield v


def gen_brute(charset=None, min_len=1, max_len=8, prefix="", suffix=""):
    if not charset:
        charset = string.ascii_lowercase + string.digits
    chars = list(dict.fromkeys(charset))
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(chars, repeat=length):
            yield prefix + "".join(combo) + suffix


def gen_master(cfg):
    mode = cfg.get("mode", "smart")
    ui   = cfg.get("user_info", {})
    gens = []

    # Always start with common passwords
    gens.append(gen_top_common())
    gens.append(gen_google_common())

    # Smart personal attack
    if mode in ("smart", "hybrid") and any(v for v in ui.values() if v):
        gens.append(gen_smart(ui))

    # Calendar attack
    if mode in ("calendar", "hybrid"):
        cal  = cfg.get("calendar", {})
        pres = list(cal.get("prefix_words") or [])
        sufs = list(cal.get("suffix_words") or [])
        if ui.get("name"):  pres.append(ui["name"])
        if ui.get("nick"):  pres.append(ui["nick"])
        if ui.get("lucky"): sufs.append(ui["lucky"])
        gens.append(gen_calendar(
            start   = int(cal.get("start_year", 1940)),
            end     = int(cal.get("end_year", 2025)),
            prefixes= pres or [""],
            suffixes= sufs or [""],
            fmts    = cal.get("date_formats") or None,
            seps    = cal.get("separators") or ["", "_", "-", ".", "/"],
        ))

    # Keyboard walks
    if mode in ("keyboard", "hybrid"):
        gens.append(gen_keyboard())

    # Dictionary / wordlists
    DATA_DIR  = Path(os.environ.get("DATA_DIR", "/tmp/zipcracker"))
    DICTS_DIR = DATA_DIR / "dictionaries"
    DICTS_DIR.mkdir(parents=True, exist_ok=True)
    wlists = [str(f) for f in DICTS_DIR.glob("*.txt")] + cfg.get("extra_wordlists", [])
    for key in cfg.get("github_lists", []):
        url = GITHUB_LISTS.get(key)
        if url: wlists.append(url)
    if wlists:
        gens.append(gen_dict_streaming(wlists))

    # Indian wordlist (always)
    gens.append(gen_indian_wordlist())

    # Mobile attack
    if mode in ("mobile", "hybrid"):
        mob = cfg.get("mobile", {})
        gens.append(gen_mobile(
            numbers       = mob.get("numbers", []),
            country_codes = mob.get("country_codes", ["+91"]),
            extras        = mob.get("extra_prefixes", []),
            density       = int(mob.get("density", 100)),
        ))

    # Brute force
    if mode in ("brute", "hybrid"):
        bf = cfg.get("brute", {})
        cs = ""
        for key in (bf.get("charsets") or ["lower", "digits"]):
            cs += CS.get(key, key)
        cs += (bf.get("custom_chars") or "")
        cs = "".join(dict.fromkeys(cs)) if cs else (string.ascii_lowercase + string.digits)
        gens.append(gen_brute(
            charset = cs,
            min_len = int(bf.get("min_len", 1)),
            max_len = int(bf.get("max_len", 8)),
            prefix  = bf.get("prefix") or "",
            suffix  = bf.get("suffix") or "",
        ))

    # De-duplicate up to cap
    seen  = set()
    count = 0
    CAP   = 10_000_000
    for gen in gens:
        for pw in gen:
            if not _ok(pw): continue
            if count < CAP:
                if pw in seen: continue
                seen.add(pw)
            count += 1
            yield pw


# ─── Cracker ─────────────────────────────────────────────────────────────────
class Cracker:
    """Parallel batch ZIP/PDF cracker for maximum speed."""

    # ── Parallel batch ZIP cracker ────────────────────────────────────────────
    @staticmethod
    def crack_zip_fast(fpath, pw_gen, progress_cb=None, freq=1000):
        res = {
            "found": False, "password": None, "attempts": 0,
            "elapsed": 0.0, "speed": 0, "cancelled": False,
            "error": None, "use_aes": False
        }
        if not Path(fpath).exists():
            res["error"] = "File not found"; return res

        names = []; use_aes = False
        try:
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        names = z.namelist()
                        if names:
                            info = z.infolist()[0]
                            use_aes = (info.flag_bits & 0x1) != 0 or info.compress_type == 99
                except:
                    pass
            if not names:
                with zipfile.ZipFile(fpath) as z:
                    names = z.namelist()
        except Exception as e:
            res["error"] = str(e); return res

        if not names:
            res["error"] = "Empty ZIP"; return res

        res["use_aes"] = use_aes
        target = names[0]
        t0     = time.time()
        ZF     = pyzipper.AESZipFile if (use_aes and HAS_AES) else zipfile.ZipFile

        # For AES (slow): single-threaded is fine
        if use_aes:
            n = 0; found = None; last = 0
            try:
                with ZF(fpath) as zf:
                    for pw in pw_gen:
                        n += 1
                        if n - last >= freq:
                            el = time.time() - t0
                            sp = int(n / max(el, 0.001))
                            last = n
                            if progress_cb and not progress_cb(n, sp, pw):
                                res["cancelled"] = True; break
                        try:
                            zf.setpassword(pw.encode("utf-8", "ignore"))
                            zf.read(target)
                            found = pw; break
                        except:
                            pass
            except Exception as e:
                res["error"] = str(e)
            el = time.time() - t0
            res.update(attempts=n, elapsed=round(el, 2), speed=int(n / max(el, 0.001)))
            if found:
                res["found"] = True; res["password"] = found
                log.info(f"AES CRACKED! '{found}' n={n:,}")
            return res

        # For standard ZIP: parallel batch cracking (genuine speed boost)
        BATCH     = 2500   # v25: larger batches for better throughput
        N_WORKERS = 8      # v25: more workers for higher speed
        stop_evt  = threading.Event()
        found_pw  = [None]
        total_n   = [0]
        lock      = threading.Lock()

        def try_batch(batch):
            if stop_evt.is_set(): return None
            try:
                zf = zipfile.ZipFile(fpath)
                for pw in batch:
                    if stop_evt.is_set(): break
                    try:
                        zf.setpassword(pw.encode("utf-8", "ignore"))
                        zf.read(target)
                        zf.close()
                        return pw
                    except:
                        pass
                zf.close()
            except:
                pass
            return None

        batch   = []
        futures = {}
        t_last  = time.time()
        n_last  = 0
        current = [""]

        try:
            with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
                for pw in pw_gen:
                    if stop_evt.is_set(): break
                    batch.append(pw)
                    current[0] = pw

                    if len(batch) >= BATCH:
                        future = ex.submit(try_batch, batch[:])
                        with lock:
                            futures[future] = len(batch)
                            total_n[0] += len(batch)
                        batch = []

                        # Check completed
                        done = [f for f in list(futures.keys()) if f.done()]
                        for f in done:
                            try:
                                result = f.result()
                                if result:
                                    found_pw[0] = result
                                    stop_evt.set()
                            except:
                                pass
                            with lock:
                                futures.pop(f, None)

                        if stop_evt.is_set(): break

                        # Progress report
                        now = time.time()
                        if now - t_last >= 1.0:
                            with lock:
                                n = total_n[0]
                            el = now - t0
                            sp = int(n / max(el, 0.001))
                            t_last = now; n_last = n
                            if progress_cb and not progress_cb(n, sp, current[0]):
                                stop_evt.set(); break

                # Try remaining batch
                if batch and not stop_evt.is_set():
                    future = ex.submit(try_batch, batch)
                    with lock:
                        futures[future] = len(batch)
                        total_n[0] += len(batch)

                # Wait for all remaining futures
                for f in list(futures.keys()):
                    try:
                        result = f.result(timeout=30)
                        if result and not found_pw[0]:
                            found_pw[0] = result
                            stop_evt.set()
                    except:
                        pass
        except Exception as e:
            res["error"] = str(e)

        el = time.time() - t0
        n  = total_n[0]
        res.update(attempts=n, elapsed=round(el, 2), speed=int(n / max(el, 0.001)))
        if found_pw[0]:
            res["found"] = True; res["password"] = found_pw[0]
            log.info(f"ZIP CRACKED! '{found_pw[0]}' n={n:,} speed={res['speed']:,}/s")
        if stop_evt.is_set() and not found_pw[0]:
            res["cancelled"] = True
        return res

    # ── PDF cracker ───────────────────────────────────────────────────────────
    @staticmethod
    def crack_pdf(fpath, pw_gen, progress_cb=None, freq=500):
        res = {
            "found": False, "password": None, "attempts": 0,
            "elapsed": 0.0, "speed": 0, "cancelled": False, "error": None
        }
        if not Path(fpath).exists():
            res["error"] = "File not found"; return res
        if not HAS_PIKE and not HAS_PDF:
            res["error"] = "pip install pikepdf pypdf"; return res

        t0 = time.time(); last = 0; found = None; n = 0
        try:
            for pw in pw_gen:
                n += 1
                if n - last >= freq:
                    el = time.time() - t0
                    sp = int(n / max(el, 0.001))
                    last = n
                    if progress_cb and not progress_cb(n, sp, pw):
                        res["cancelled"] = True; break
                if HAS_PIKE:
                    try:
                        with pikepdf.open(fpath, password=pw):
                            found = pw; break
                    except pikepdf.PasswordError:
                        pass
                    except:
                        pass
                elif HAS_PDF:
                    try:
                        r = _PDF(fpath)
                        if r.is_encrypted and r.decrypt(pw) != 0:
                            found = pw; break
                    except:
                        pass
        except Exception as e:
            res["error"] = str(e)

        el = time.time() - t0
        res.update(attempts=n, elapsed=round(el, 2), speed=int(n / max(el, 0.001)))
        if found:
            res["found"] = True; res["password"] = found
            log.info(f"PDF CRACKED! '{found}'")
        return res

    @staticmethod
    def crack(fpath, pw_gen, progress_cb=None, freq=1000):
        ext = Path(fpath).suffix.lower()
        if ext == ".pdf":
            return Cracker.crack_pdf(fpath, pw_gen, progress_cb, freq)
        return Cracker.crack_zip_fast(fpath, pw_gen, progress_cb, freq)

    @staticmethod
    def extract_and_zip(fpath, password, out_zip):
        res = {"ok": False, "zip_path": None, "files": [], "error": None}
        tmp = tempfile.mkdtemp()
        try:
            pw_b = password.encode("utf-8", "ignore")
            if HAS_AES:
                try:
                    with pyzipper.AESZipFile(fpath) as z:
                        z.setpassword(pw_b)
                        z.extractall(tmp)
                        res["files"] = z.namelist()
                except:
                    with zipfile.ZipFile(fpath) as z:
                        z.setpassword(pw_b)
                        z.extractall(tmp)
                        res["files"] = z.namelist()
            else:
                with zipfile.ZipFile(fpath) as z:
                    z.setpassword(pw_b)
                    z.extractall(tmp)
                    res["files"] = z.namelist()
            shutil.make_archive(out_zip.replace(".zip", ""), "zip", tmp)
            res["ok"] = True; res["zip_path"] = out_zip
        except Exception as e:
            res["error"] = str(e)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return res
