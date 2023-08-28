---
title: '{{escaped_title | safe}}'
date: {{date}}
slug: '/{{slug}}'
tags:{% for tag in tags %}
  - {{tag}}{% endfor %}
---
# {{title | safe}}

https://{{url | safe}}

{% for annotation in annotations %}---
{% if annotation.comment %}_{{annotation.comment | safe}}_ {% endif %}{{annotation.body | safe}}^{{annotation.id}}
{% endfor %}
