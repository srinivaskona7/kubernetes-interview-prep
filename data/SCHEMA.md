# Chapter JSON contract — data/chN.json
{
 "number": 1, "title": "...", "part": "Part 1 · Introduction", "tagline": "one line, <=90 chars",
 "overview": "2-3 sentence plain-English chapter summary",
 "topics": [ {                      // 10-16 topics per chapter, each = one interview question
   "id": "ch1-what-is-a-container",  // unique, kebab-case, prefixed chN-
   "level": "junior|mid|senior",
   "question": "as an interviewer would ask it",
   "say_first": "1-2 sentence answer to open with",
   "explain": ["short paragraph or step", "..."],          // 2-5 items, plain words, analogies welcome
   "key_points": ["..."],                                   // 3-6 bullets
   "table": {"caption":"", "headers":["",""], "rows":[["",""]]},   // optional, use when comparing
   "commands": [{"cmd":"kubectl ...","note":"what it shows"}],     // optional, real, correct kubectl/yaml one-liners
   "diagram": {"file":"diagrams/ch1-xxx.html","title":"","ratio":"1100/620"},  // optional, ratio = viewBox w/h
   "follow_ups": ["likely next question"],                  // 1-3
   "pitfalls": ["common wrong answer or mistake"]           // 0-3
 } ],
 "diagrams": ["diagrams/ch1-xxx.html", ...]   // every diagram file produced for the chapter
}
Rules: write in your own words (paraphrase; no copied sentences). Never mention the source book, its title, publisher or any author. No emoji. Valid JSON only.
