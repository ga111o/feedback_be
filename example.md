```json
// multiple choice
{
  "survey_id": "123",
  "question_text": "선호하는 프로그래밍 언어는?",
  "question_type": "multiple_choice",
  "options": [
    { "value": "python", "label": "Python 언어" },
    { "value": "javascript", "label": "JavaScript" },
    { "value": "java", "label": "Java" }
  ],
  "order": 1,
  "is_required": true
}
```

```json
// checkboxes
{
  "survey_id": "123",
  "question_text": "사용해본 기술은?",
  "question_type": "checkboxes",
  "options": [
    { "value": "react", "label": "React.js" },
    { "value": "vue", "label": "Vue.js" },
    { "value": "angular", "label": "Angular" }
  ],
  "order": 2,
  "is_required": true
}
```

```json
// rating
{
  "survey_id": "123",
  "question_text": "서비스 만족도",
  "question_type": "rating",
  "rating_min": 1,
  "rating_max": 5,
  "rating_labels": {
    "1": "매우 불만족",
    "3": "보통",
    "5": "매우 만족"
  },
  "order": 3,
  "is_required": true
}
```
