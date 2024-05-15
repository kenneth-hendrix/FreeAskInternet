import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'https://jackh.beer/api';

  constructor(private http: HttpClient) { }

  getModels(): Observable<any> {
    return this.http.get(`${this.apiUrl}/v1/models`);
  }

  postChatCompletion(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/v1/chat/completions`, data);
  }

  getSearchRefs(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/search/get_search_refs`, data);
  }

  streamSearchResults(search_uuid: string, data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/search/stream/${search_uuid}`, data, {
      responseType: 'text',
    });
  }
}
