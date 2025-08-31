# Canonical URL Patterns for Music Reference Sources

## Current Working Sources ✅

### Billboard
- **Pattern**: `https://www.billboard.com/music/news/{artist-slug}-influence-analysis`
- **Example**: `https://www.billboard.com/music/news/50-cent-influence-analysis`
- **Status**: ✅ Working in production API

### Pitchfork  
- **Pattern**: `https://pitchfork.com/features/{artist-slug}-influence-analysis`
- **Example**: `https://pitchfork.com/features/taylor-swift-influence-analysis`
- **Status**: ✅ Working in production API

## Podcast Sources (Need URL Mapping) 🔧

### NPR Fresh Air
- **Pattern**: `https://www.npr.org/{year}/{month}/{day}/{episode-id}/{episode-slug}`
- **Example**: `https://www.npr.org/2023/09/05/1197628068/mark-ronson-on-the-barbie-soundtrack-score`
- **Current Issue**: Episode IDs in data (184977556) don't match NPR URL format
- **Status**: ⚠️ Using fake .txt.com URLs

### NPR All Songs Considered
- **Pattern**: `https://www.npr.org/{year}/{month}/{day}/{episode-id}/{episode-slug}`
- **Example**: `https://www.npr.org/2023/04/07/1168394032/new-music-friday`
- **Status**: ⚠️ Using fake .txt.com URLs

### Broken Record Podcast
- **Pattern**: `https://brokenrecordpodcast.com/episode/{episode-slug}`
- **Example**: `https://brokenrecordpodcast.com/episode/mark-ronson`
- **Status**: ⚠️ Using fake .txt.com URLs

## Recommended Reference Sources (Not Yet Integrated) 📋

### Wikipedia
- **Artist Pattern**: `https://en.wikipedia.org/wiki/{Artist_Name}`
- **Album Pattern**: `https://en.wikipedia.org/wiki/{Album_Name}`
- **Examples**: 
  - `https://en.wikipedia.org/wiki/The_Beatles`
  - `https://en.wikipedia.org/wiki/Abbey_Road`
- **Benefits**: Comprehensive biographical data, discography, influence information
- **Status**: 🔄 Recommend adding to data collection

### MusicBrainz
- **Artist Pattern**: `https://musicbrainz.org/artist/{mbid}`
- **Album Pattern**: `https://musicbrainz.org/release-group/{mbid}`
- **Examples**:
  - `https://musicbrainz.org/artist/b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d` (The Beatles)
  - `https://musicbrainz.org/release-group/7c1014eb-454c-3867-8854-3c95d265f8de` (Abbey Road)
- **Benefits**: Structured metadata, relationships, precise identifiers
- **Status**: 🔄 Recommend adding to data collection

### AllMusic
- **Artist Pattern**: `https://www.allmusic.com/artist/{artist-slug}-mn{id}`
- **Album Pattern**: `https://www.allmusic.com/album/{album-slug}-mw{id}`
- **Examples**:
  - `https://www.allmusic.com/artist/the-beatles-mn0000754032`
  - `https://www.allmusic.com/album/abbey-road-mw0000418025`
- **Benefits**: Professional reviews, detailed discographies, genre classification
- **Status**: 🔄 Recommend adding to data collection

### Discogs
- **Artist Pattern**: `https://www.discogs.com/artist/{id}-{Artist-Name}`
- **Release Pattern**: `https://www.discogs.com/release/{id}`
- **Examples**:
  - `https://www.discogs.com/artist/82730-The-Beatles`
  - `https://www.discogs.com/release/448131-The-Beatles-Abbey-Road`
- **Benefits**: Comprehensive release data, marketplace information, user reviews
- **Status**: 🔄 Recommend adding to data collection

### Genius
- **Artist Pattern**: `https://genius.com/artists/{Artist-slug}`
- **Song Pattern**: `https://genius.com/{Artist-slug}-{song-slug}-lyrics`
- **Examples**:
  - `https://genius.com/artists/The-beatles`
  - `https://genius.com/The-beatles-come-together-lyrics`
- **Benefits**: Lyric analysis, song meanings, cultural context
- **Status**: 🔄 Recommend adding to data collection

## Implementation Priority

### Phase 1: Fix Existing Sources 🚀
1. **Podcast URL Mapping**: Create mapping from episode IDs to real NPR/podcast URLs
2. **Validation**: Ensure all Billboard/Pitchfork URLs are working correctly

### Phase 2: Add Reference Sources 📚
1. **Wikipedia Integration**: Add Wikipedia pages for all artists in knowledge graph
2. **MusicBrainz Integration**: Add structured metadata and relationships
3. **AllMusic Integration**: Add professional reviews and detailed discographies

### Phase 3: Enhanced Sources 🎯
1. **Discogs**: Marketplace and release data
2. **Genius**: Lyrical analysis and cultural context
3. **Last.fm**: User listening data and similar artists

## Benefits of Canonical URLs

- **User Trust**: Real links to authoritative sources
- **SEO Value**: Proper attribution improves search ranking
- **Research Capability**: Users can dive deeper into sources
- **Professional Credibility**: Links to Wikipedia, MusicBrainz establish authority
- **Cross-Reference**: Multiple sources provide comprehensive view

## Current API Status

**✅ Working**: Billboard and Pitchfork return real canonical URLs
**⚠️ Partial**: Podcast sources need URL mapping  
**🔄 Missing**: Wikipedia, MusicBrainz, AllMusic, Discogs, Genius not yet integrated