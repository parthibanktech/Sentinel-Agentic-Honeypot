import { Injectable } from '@angular/core';
import { FinalCallbackPayload } from '../types';
import { HttpClient } from '@angular/common/http';
import { of, delay } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CallbackService {
  
  // In a real app, inject HttpClient. Here we simulate the request.
  // constructor(private http: HttpClient) {}

  async sendFinalResult(payload: FinalCallbackPayload): Promise<boolean> {
    console.log('[CallbackService] Reporting Final Result to Hub:', payload);
    
    // Simulate API Latency
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Simulate Success
    console.log('[CallbackService] Report Successful (200 OK)');
    return true;
  }
}