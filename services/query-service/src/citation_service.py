"""
Citation Service for Query Service
Provides comprehensive citation formatting, source verification, and attribution services
"""

import logging
import re
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from enum import Enum

from contracts import SearchResult

logger = logging.getLogger(__name__)

class CitationStyle(str, Enum):
    """Supported citation styles"""
    APA = "apa"
    MLA = "mla" 
    CHICAGO = "chicago"
    IEEE = "ieee"
    HARVARD = "harvard"
    BASIC = "basic"

@dataclass
class SourceVerification:
    """Source verification result"""
    url: str
    is_accessible: bool
    status_code: Optional[int] = None
    last_checked: Optional[datetime] = None
    redirect_url: Optional[str] = None
    domain_credibility: Optional[float] = None
    ssl_valid: bool = False
    error_message: Optional[str] = None

@dataclass
class FormattedCitation:
    """Formatted citation with metadata"""
    citation: str
    style: CitationStyle
    entities: List[str]
    confidence: float
    source_verified: bool
    verification: Optional[SourceVerification] = None

class CitationService:
    """Service for citation formatting and source verification"""
    
    def __init__(self):
        self.verification_cache = {}  # URL -> SourceVerification cache
        self.credible_domains = {
            # High credibility sources
            'pitchfork.com': 0.95,
            'npr.org': 0.98,
            'rollingstone.com': 0.90,
            'allmusic.com': 0.85,
            'billboard.com': 0.88,
            'theguardian.com': 0.92,
            'nytimes.com': 0.95,
            'washingtonpost.com': 0.93,
            'bbc.com': 0.96,
            'reuters.com': 0.94,
            
            # Medium credibility
            'wikipedia.org': 0.75,
            'genius.com': 0.70,
            'discogs.com': 0.80,
            'last.fm': 0.65,
            
            # Default for unknown domains
            'default': 0.50
        }
        
    async def format_citation(
        self, 
        search_result: SearchResult,
        style: CitationStyle = CitationStyle.APA,
        include_entities: bool = True,
        verify_source: bool = True
    ) -> FormattedCitation:
        """
        Format a citation from a search result
        
        Args:
            search_result: Search result to cite
            style: Citation style to use
            include_entities: Include entity information
            verify_source: Verify source accessibility
            
        Returns:
            Formatted citation with metadata
        """
        logger.info(f"Formatting citation in {style.value} style")
        
        # Verify source if requested
        verification = None
        if verify_source and search_result.source_info.url:
            verification = await self.verify_source(search_result.source_info.url)
        
        # Generate citation based on style
        citation_text = self._generate_citation_text(search_result, style)
        
        # Calculate confidence based on attribution completeness and source verification
        confidence = self._calculate_citation_confidence(search_result, verification)
        
        return FormattedCitation(
            citation=citation_text,
            style=style,
            entities=search_result.entities,
            confidence=confidence,
            source_verified=verification.is_accessible if verification else False,
            verification=verification
        )
    
    async def format_multiple_citations(
        self,
        search_results: List[SearchResult],
        style: CitationStyle = CitationStyle.APA,
        deduplicate: bool = True,
        min_confidence: float = 0.7
    ) -> List[FormattedCitation]:
        """Format multiple citations efficiently"""
        logger.info(f"Formatting {len(search_results)} citations")
        
        # Filter by confidence if specified
        if min_confidence > 0:
            search_results = [r for r in search_results if r.attribution_completeness >= min_confidence]
        
        # Format citations concurrently
        tasks = [
            self.format_citation(result, style, verify_source=True)
            for result in search_results
        ]
        
        citations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and failed citations
        valid_citations = [c for c in citations if isinstance(c, FormattedCitation)]
        
        # Deduplicate by source if requested
        if deduplicate:
            valid_citations = self._deduplicate_citations(valid_citations)
        
        logger.info(f"Generated {len(valid_citations)} valid citations")
        return valid_citations
    
    async def verify_source(self, url: str) -> SourceVerification:
        """
        Enhanced source accessibility and credibility verification
        
        Args:
            url: Source URL to verify
            
        Returns:
            Source verification result with enhanced validation
        """
        # Check cache first
        if url in self.verification_cache:
            cached = self.verification_cache[url]
            # Use cache if less than 1 hour old
            if (datetime.now(timezone.utc) - cached.last_checked).seconds < 3600:
                return cached
        
        logger.info(f"Verifying source with enhanced validation: {url}")
        
        verification = SourceVerification(
            url=url,
            is_accessible=False,
            last_checked=datetime.now(timezone.utc)
        )
        
        try:
            # Enhanced URL validation
            if not self._is_valid_url(url):
                verification.error_message = "Invalid URL format"
                return verification
            
            # Parse URL for domain analysis
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            verification.domain_credibility = self.credible_domains.get(
                domain, self.credible_domains['default']
            )
            
            # Enhanced SSL checking
            verification.ssl_valid = parsed.scheme == 'https'
            if not verification.ssl_valid and domain in self.credible_domains:
                logger.warning(f"High-credibility domain {domain} not using HTTPS")
            
            # Enhanced HTTP request with headers and timeout
            headers = {
                'User-Agent': 'UT-Citation-Validator/1.0 (Academic Research)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                start_time = datetime.now(timezone.utc)
                
                # Try HEAD first for efficiency, fallback to GET if needed
                try:
                    async with session.head(url, allow_redirects=True) as response:
                        await self._process_response(verification, response, start_time)
                except aiohttp.ClientResponseError:
                    # Some servers don't support HEAD, try GET
                    async with session.get(url, allow_redirects=True) as response:
                        await self._process_response(verification, response, start_time)
                    
        except aiohttp.ClientError as e:
            verification.error_message = f"Client error: {str(e)}"
            logger.warning(f"Client error verifying {url}: {e}")
        except asyncio.TimeoutError:
            verification.error_message = "Request timeout - server may be slow or unresponsive"
            logger.warning(f"Timeout verifying {url}")
        except Exception as e:
            verification.error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Error verifying {url}: {e}")
        
        # Cache result with enhanced metadata
        self.verification_cache[url] = verification
        
        return verification
    
    def _is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        try:
            parsed = urlparse(url)
            return all([
                parsed.scheme in ['http', 'https'],
                parsed.netloc,
                len(parsed.netloc) > 0,
                '.' in parsed.netloc,  # Has domain extension
                not any(char in parsed.netloc for char in ['<', '>', '"', "'"])  # No suspicious chars
            ])
        except:
            return False
    
    async def _process_response(self, verification: SourceVerification, response, start_time):
        """Process HTTP response with enhanced analysis"""
        verification.status_code = response.status
        verification.is_accessible = 200 <= response.status < 400
        
        # Track response time
        response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Track redirects with validation
        if str(response.url) != verification.url:
            verification.redirect_url = str(response.url)
            # Validate redirect URL
            if not self._is_valid_url(verification.redirect_url):
                verification.error_message = "Redirected to invalid URL"
                verification.is_accessible = False
        
        # Enhanced response analysis
        content_type = response.headers.get('content-type', '').lower()
        if verification.is_accessible:
            # Check if it's likely a valid web page
            valid_content_types = ['text/html', 'text/plain', 'application/xhtml']
            if not any(ct in content_type for ct in valid_content_types):
                logger.info(f"Unusual content type for {verification.url}: {content_type}")
            
            # Check for suspicious response headers
            if 'x-robots-tag' in response.headers and 'noindex' in response.headers.get('x-robots-tag', ''):
                logger.info(f"Source {verification.url} has noindex directive")
        
        # Log slow responses
        if response_time > 5:
            logger.warning(f"Slow response from {verification.url}: {response_time:.2f}s")
    
    def _generate_citation_text(
        self, 
        search_result: SearchResult, 
        style: CitationStyle
    ) -> str:
        """Generate citation text based on style"""
        
        source_info = search_result.source_info
        
        # Extract information
        author = source_info.author or "Unknown Author"
        title = source_info.title or "Untitled"
        source = source_info.source or "Unknown Source"
        url = source_info.url
        published_date = source_info.published_date
        
        # Format date
        date_str = ""
        if published_date:
            if style == CitationStyle.APA:
                date_str = f"({published_date.year})"
            elif style == CitationStyle.MLA:
                date_str = f"{published_date.strftime('%d %b %Y')}"
            elif style == CitationStyle.CHICAGO:
                date_str = f"{published_date.strftime('%B %d, %Y')}"
        
        # Generate citation by style
        if style == CitationStyle.APA:
            citation = f"{author} {date_str}. {title}. {source}."
            if url:
                citation += f" Retrieved from {url}"
                
        elif style == CitationStyle.MLA:
            citation = f'{author}. "{title}." {source}'
            if date_str:
                citation += f", {date_str}"
            citation += "."
            if url:
                citation += f" Web. {datetime.now().strftime('%d %b %Y')}."
                
        elif style == CitationStyle.CHICAGO:
            citation = f'{author}. "{title}." {source}'
            if date_str:
                citation += f", {date_str}"
            citation += "."
            if url:
                citation += f" {url}."
                
        elif style == CitationStyle.IEEE:
            citation = f'{author}, "{title}," {source}'
            if date_str:
                citation += f", {published_date.year}"
            citation += "."
            if url:
                citation += f" [Online]. Available: {url}"
                
        elif style == CitationStyle.HARVARD:
            citation = f"{author} {date_str} '{title}', {source}"
            if url:
                citation += f", viewed {datetime.now().strftime('%d %B %Y')}, <{url}>"
            citation += "."
            
        else:  # BASIC
            citation = f'"{title}" by {author}, {source}'
            if url:
                citation += f" - {url}"
        
        # Add entity context if available
        if search_result.entities and len(search_result.entities) > 0:
            entity_context = f" [Mentions: {', '.join(search_result.entities[:3])}]"
            citation += entity_context
        
        return citation
    
    def _calculate_citation_confidence(
        self,
        search_result: SearchResult,
        verification: Optional[SourceVerification]
    ) -> float:
        """Calculate confidence score for citation"""
        
        confidence = 0.0
        
        # Base confidence from attribution completeness
        confidence += search_result.attribution_completeness * 0.4
        
        # Source information completeness
        source_info = search_result.source_info
        info_score = 0.0
        
        if source_info.author:
            info_score += 0.25
        if source_info.title:
            info_score += 0.25
        if source_info.published_date:
            info_score += 0.25
        if source_info.url:
            info_score += 0.25
            
        confidence += info_score * 0.3
        
        # Source verification
        if verification:
            if verification.is_accessible:
                confidence += 0.15
            if verification.ssl_valid:
                confidence += 0.05
            if verification.domain_credibility:
                confidence += verification.domain_credibility * 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_citations(
        self, 
        citations: List[FormattedCitation]
    ) -> List[FormattedCitation]:
        """Remove duplicate citations by source"""
        
        seen_sources = set()
        unique_citations = []
        
        # Sort by confidence to keep best citations
        sorted_citations = sorted(citations, key=lambda c: c.confidence, reverse=True)
        
        for citation in sorted_citations:
            # Create source signature from URL or title+author
            if citation.verification and citation.verification.url:
                source_sig = citation.verification.url
            else:
                # Fallback to title+author combination
                source_sig = f"{citation.citation[:50]}..."  # First 50 chars as signature
            
            if source_sig not in seen_sources:
                seen_sources.add(source_sig)
                unique_citations.append(citation)
        
        return unique_citations
    
    async def get_citation_suggestions(
        self,
        query: str,
        search_results: List[SearchResult],
        max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get citation suggestions for a query
        
        Returns suggested citations with context
        """
        logger.info(f"Getting citation suggestions for query: {query}")
        
        # Filter for high-quality results
        quality_results = [
            r for r in search_results 
            if r.citation_ready and r.attribution_completeness > 0.7
        ]
        
        # Sort by relevance and quality
        sorted_results = sorted(
            quality_results,
            key=lambda r: (r.similarity_score * r.attribution_completeness),
            reverse=True
        )[:max_suggestions]
        
        # Generate citations
        suggestions = []
        for i, result in enumerate(sorted_results):
            citation = await self.format_citation(result, CitationStyle.APA, verify_source=True)
            
            suggestions.append({
                'rank': i + 1,
                'citation': citation.citation,
                'confidence': citation.confidence,
                'entities': citation.entities,
                'source_verified': citation.source_verified,
                'excerpt': result.excerpt or result.content[:200],
                'relevance_score': result.similarity_score,
                'attribution_completeness': result.attribution_completeness,
                'source_url': result.source_info.url
            })
        
        logger.info(f"Generated {len(suggestions)} citation suggestions")
        return suggestions
    
    async def bulk_verify_sources(
        self, 
        urls: List[str],
        max_concurrent: int = 10
    ) -> Dict[str, SourceVerification]:
        """Bulk verify multiple sources with concurrency control"""
        
        logger.info(f"Bulk verifying {len(urls)} sources")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def verify_with_semaphore(url):
            async with semaphore:
                return url, await self.verify_source(url)
        
        # Run verifications concurrently
        tasks = [verify_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        verifications = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                url, verification = result
                verifications[url] = verification
            elif isinstance(result, Exception):
                logger.error(f"Error in bulk verification: {result}")
        
        logger.info(f"Completed bulk verification of {len(verifications)} sources")
        return verifications
    
    def get_domain_credibility(self, url: str) -> float:
        """Get credibility score for a domain"""
        try:
            domain = urlparse(url).netloc.lower()
            return self.credible_domains.get(domain, self.credible_domains['default'])
        except:
            return self.credible_domains['default']