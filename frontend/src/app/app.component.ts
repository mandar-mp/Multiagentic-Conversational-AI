import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from './chat.service';
import { ChatMessage } from './models/chat-message';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Gemini Chat';
  messages: ChatMessage[] = [];
  inputText = '';
  conversationId = '';
  isSending = false;
  statusMessage = 'Ready to chat';

  constructor(private chatService: ChatService) {}

  sendMessage(): void {
    const trimmed = this.inputText.trim();
    if (!trimmed || this.isSending) {
      return;
    }

    this.isSending = true;
    this.statusMessage = 'Waiting for Gemini response…';

    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString()
    };

    this.messages = [...this.messages, userMessage];
    this.inputText = '';

    this.chatService.sendMessage({
      message: trimmed,
      conversation_id: this.conversationId || undefined
    }).subscribe({
      next: response => {
        this.conversationId = response.conversation_id;
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString()
        };
        this.messages = [...this.messages, assistantMessage];
        this.statusMessage = `Gemini replied with ${response.metadata?.model ?? 'model'}`;
        this.isSending = false;
        setTimeout(() => this.scrollToBottom(), 50);
      },
      error: error => {
        const errorText = error?.error?.detail || error.message || 'Unknown error';
        this.statusMessage = `Error: ${errorText}`;
        this.isSending = false;
      }
    });
  }

  clearConversation(): void {
    this.messages = [];
    this.conversationId = '';
    this.statusMessage = 'Conversation reset. Start a new chat.';
  }

  private scrollToBottom(): void {
    const container = document.querySelector('.conversation');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
