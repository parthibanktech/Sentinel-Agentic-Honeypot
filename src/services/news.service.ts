import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NewsService {
  private http: HttpClient = inject(HttpClient);
  
  // Switch to 'search' (relevance) instead of 'search_by_date' for better result matching
  private baseUrl = 'https://hn.algolia.com/api/v1/search';

  async getHeadlines(userKeyword: string = ''): Promise<any> {
    const term = userKeyword ? userKeyword.trim() : '';
    
    // Simpler logic:
    // 1. If user types a keyword, search strictly for that (e.g. "crypto") to guarantee results.
    // 2. If empty, search for a broad security topic.
    
    const query = term || 'cybersecurity scam';

    const params = new HttpParams()
      .set('query', query)
      .set('tags', 'story')
      .set('hitsPerPage', '20');
    
    console.log(`[NewsService] Fetching: ${this.baseUrl}?${params.toString()}`);

    return lastValueFrom(this.http.get<any>(this.baseUrl, { params }));
  }
}