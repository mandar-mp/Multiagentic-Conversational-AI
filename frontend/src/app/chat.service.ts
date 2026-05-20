import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  status: string;
  response: string;
  conversation_id: string;
  metadata: Record<string, unknown>;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiPrefix = environment.apiUrl;

  constructor(private http: HttpClient) {}

  sendMessage(payload: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiPrefix}/chat`, payload);
  }
}
