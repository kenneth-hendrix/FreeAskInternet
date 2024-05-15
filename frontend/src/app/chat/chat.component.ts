import { Component } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  query: string = '';
  response: string = '';

  constructor(private apiService: ApiService) { }

  sendQuery() {
    const request = {
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: this.query }],
      temperature: 0.7,
      max_length: 100
    };

    this.apiService.postChatCompletion(request).subscribe(
      (res: any) => {
        this.response = res.choices[0].message.content;
      },
      (err) => {
        console.error(err);
      }
    );
  }
}
