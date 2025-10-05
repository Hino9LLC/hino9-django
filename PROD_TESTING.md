# Production Testing Checklist

Comprehensive testing checklist for validating the Django news site after deployment.

**Target Site:** `YOUR_PRODUCTION_DOMAIN`

---

## 1. Basic Functionality

### Homepage & Navigation
- [ ] Homepage loads without errors
- [ ] Navigation menu works (Latest News, Tags, Search)
- [ ] Mobile menu functions correctly
- [ ] Footer links work (Privacy, Terms)

### Article Pages
- [ ] Article detail pages load correctly
- [ ] Images display properly with responsive sizing
- [ ] Article metadata shows (date, tags)
- [ ] Tag links navigate correctly
- [ ] Back navigation preserves context (from search, from tag page, pagination)

### Search Functionality
- [ ] Search page loads
- [ ] Vector search returns relevant results
- [ ] Text search returns relevant results
- [ ] Hybrid search combines both approaches
- [ ] Search type switching works
- [ ] Empty search handled gracefully
- [ ] Special characters in queries handled properly
- [ ] Rate limiting activates appropriately (100/hour)

### Tag System
- [ ] Tags index page loads
- [ ] Tag detail pages show correct articles
- [ ] Tag filtering works
- [ ] Pagination on tag pages functions
- [ ] Tag counts display accurately

### Pagination
- [ ] Page navigation works (Next/Previous, page numbers)
- [ ] First and last pages accessible
- [ ] Navigation context preserved (search query, tag, etc.)

---

## 2. Performance Testing

### Lighthouse (Chrome DevTools)

**Target Scores:**
- [ ] Performance: ≥ 90
- [ ] Accessibility: ≥ 90
- [ ] Best Practices: ≥ 90
- [ ] SEO: ≥ 90

**Key Metrics:**
- [ ] Time to Interactive (TTI) < 3.8s
- [ ] First Contentful Paint (FCP) < 1.8s
- [ ] Cumulative Layout Shift (CLS) < 0.1
- [ ] Largest Contentful Paint (LCP) < 2.5s

### PageSpeed Insights
**URL:** https://pagespeed.web.dev/

**Tests:**
- [ ] Mobile performance score > 90
- [ ] Desktop performance score > 95
- [ ] Core Web Vitals passed
- [ ] Server response time < 600ms
- [ ] Images optimized

---

## 3. SEO Validation

### Google Rich Results Test
**URL:** https://search.google.com/test/rich-results

**Tests:**
- [ ] NewsArticle structured data detected
- [ ] No errors in JSON-LD
- [ ] All required properties present (headline, image, date, author)
- [ ] Preview renders correctly

### Schema.org Validator
**URL:** https://validator.schema.org/

**Tests:**
- [ ] Valid JSON-LD syntax
- [ ] NewsArticle type recognized
- [ ] No warnings/errors

### Social Media Sharing

**Facebook Debugger** (https://developers.facebook.com/tools/debug/)
- [ ] og:title displays correctly
- [ ] og:description present
- [ ] og:image loads and displays
- [ ] og:type = article
- [ ] Preview looks correct

**Twitter Card Validator** (https://cards-dev.twitter.com/validator)
- [ ] Card type: summary_large_image
- [ ] Title, description, image display correctly
- [ ] Preview renders properly

### Technical SEO

**Sitemap (`/sitemap.xml`):**
- [ ] Sitemap loads without errors
- [ ] Valid XML syntax
- [ ] Article URLs included
- [ ] Tag URLs included
- [ ] Dates and priorities set correctly

**Robots.txt (`/robots.txt`):**
- [ ] File loads successfully
- [ ] Sitemap reference present
- [ ] Admin area disallowed
- [ ] Important pages not blocked

**Canonical URLs:**
- [ ] Every page has canonical link tag
- [ ] Canonical URLs are absolute (https://)
- [ ] Self-referential on unique pages

**Meta Tags:**
- [ ] Title tags unique and descriptive
- [ ] Meta descriptions present
- [ ] Open Graph tags on all pages
- [ ] Twitter Card tags present

---

## 4. Security & SSL

### SSL Labs Test
**URL:** https://www.ssllabs.com/ssltest/

**Target:**
- [ ] Grade: A or A+
- [ ] Certificate valid and not expiring soon
- [ ] TLS 1.2+ supported
- [ ] Strong cipher suites

### Security Headers
**URL:** https://securityheaders.com/

**Required Headers:**
- [ ] Strict-Transport-Security (HSTS)
- [ ] X-Frame-Options
- [ ] X-Content-Type-Options
- [ ] Content-Security-Policy
- [ ] Referrer-Policy

**Target Grade:** A or higher

---

## 5. Accessibility

### WAVE (WebAIM)
**URL:** https://wave.webaim.org/

**Tests:**
- [ ] No errors
- [ ] Minimal warnings
- [ ] Proper heading structure (h1 → h2 → h3)
- [ ] Alt text on images
- [ ] Sufficient color contrast
- [ ] ARIA labels where appropriate

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Focus indicators visible
- [ ] No keyboard traps
- [ ] Enter/Space activate buttons/links

### Screen Reader Testing
- [ ] Page title announced
- [ ] Headings navigable
- [ ] Links descriptive
- [ ] Images have alt text
- [ ] Landmarks identified (nav, main, footer)

---

## 6. Mobile & Responsive

### Google Mobile-Friendly Test
**URL:** https://search.google.com/test/mobile-friendly

**Tests:**
- [ ] Page is mobile-friendly
- [ ] Text readable without zooming
- [ ] Content fits screen
- [ ] Links not too close together

### Responsive Testing

**Test Sizes:**
- [ ] Mobile (375px) - iPhone SE
- [ ] Mobile (390px) - iPhone 12/13
- [ ] Tablet (768px) - iPad
- [ ] Desktop (1920px) - Standard desktop
- [ ] Large desktop (2560px) - 4K displays

**Tests per Size:**
- [ ] Layout renders correctly
- [ ] Images scale properly
- [ ] Navigation accessible
- [ ] No horizontal scroll

### Real Device Testing
- [ ] iOS Safari (iPhone)
- [ ] Android Chrome
- [ ] Tablet (iPad or Android)
- [ ] Desktop browsers (Chrome, Firefox, Safari)

---

## 7. Browser Compatibility

**Test Browsers:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

**Tests:**
- [ ] Page loads without errors
- [ ] Layout correct
- [ ] Functionality works
- [ ] No console errors

---

## 8. Error Handling

### Error Pages
**Test:**
- [ ] 404 page displays for nonexistent URLs
- [ ] 404 page styled correctly
- [ ] Links back to homepage work
- [ ] No sensitive information exposed

### Rate Limiting
- [ ] Search rate limit activates at 100/hour
- [ ] User sees appropriate message
- [ ] Normal use not affected

---

## 9. Content Validation

### Content Display
- [ ] All articles display correctly
- [ ] No placeholder/test content
- [ ] Images load (no 404s)
- [ ] Dates formatted correctly
- [ ] Tags display and link properly

### Caching
- [ ] Pages load quickly (< 500ms)
- [ ] Cache headers present
- [ ] Repeated visits faster (browser cache working)

---

## 10. Health Check

**Endpoint:** `/health`

**Tests:**
- [ ] Returns 200 OK
- [ ] Returns JSON: `{"status": "healthy"}`
- [ ] No authentication required
- [ ] Responds quickly (< 100ms)

---

## Quick Validation Script

For rapid testing after deployment:

```bash
#!/bin/bash
SITE="YOUR_PRODUCTION_URL"

echo "🧪 Quick Production Test"
echo "========================"

# Health check
echo "✓ Health Check:"
curl -s $SITE/health

# Homepage
echo "✓ Homepage:"
curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" $SITE/

# Sitemap
echo "✓ Sitemap:"
curl -s -o /dev/null -w "Status: %{http_code}\n" $SITE/sitemap.xml

# Robots.txt
echo "✓ Robots.txt:"
curl -s -o /dev/null -w "Status: %{http_code}\n" $SITE/robots.txt

echo ""
echo "✅ Basic checks complete"
```

---

## Testing Tools

### Performance
- **Lighthouse**: Chrome DevTools
- **PageSpeed Insights**: https://pagespeed.web.dev/
- **WebPageTest**: https://www.webpagetest.org/

### SEO
- **Google Rich Results**: https://search.google.com/test/rich-results
- **Schema Validator**: https://validator.schema.org/
- **Facebook Debugger**: https://developers.facebook.com/tools/debug/
- **Twitter Card Validator**: https://cards-dev.twitter.com/validator

### Security
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Security Headers**: https://securityheaders.com/

### Accessibility
- **WAVE**: https://wave.webaim.org/
- **axe DevTools**: Browser extension

### Mobile
- **Google Mobile-Friendly**: https://search.google.com/test/mobile-friendly
- **BrowserStack**: https://www.browserstack.com/ (cross-browser testing)

---

*Last Updated: 2025-10-04*
