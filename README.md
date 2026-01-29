# SEO & schema (ready for future marketability)
(JSON‑LD blocks that swap by page type)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Luis Alberto Mejia Clavijo",
  "url": "{{ site.url }}",
  "description": "Expert in cognitive aesthetics of systems; poetry, image‑text, songs, sculpture, theory."
}
</script>
{% if page.schema_type == "Poem" %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Poem",
  "name": "{{ page.title | escape }}",
  "author": { "@type": "Person", "name": "Luis Alberto Mejia Clavijo" },
  "inLanguage": "es-ES",
  "datePublished": "{{ page.date | date_to_xmlschema }}",
  "description": "{{ page.excerpt | strip_html | escape }}"
}
</script>
{% endif %}

