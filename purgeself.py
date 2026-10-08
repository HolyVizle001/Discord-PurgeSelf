#!/usr/bin/env python3
"""
PurgeSelf v1.0.0 - Discord Self-Message Purge Tool
Made by HolyVizle001 on GitHub: https://github.com/HolyVizle001

Bulk delete your own Discord messages from specific DMs or entire servers.
Strict rate limiting included to minimize detection risk.

NOTE: Self-bots violate Discord's Terms of Service. 
Your account may be banned. Use at your own risk.
"""

import requests
import time
import sys
import random
from datetime import datetime

__version__ = "1.0.0"
__author__ = "HolyVizle001"
__github__ = "https://github.com/HolyVizle001"


class DiscordMessageDeleter:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.base_url = 'https://discord.com/api/v9'
        self.deleted_count = 0
        self.failed_count = 0
        self.rate_limit_hits = 0
        
        # Strict rate limiting config
        self.min_delay = 0.9
        self.max_delay = 2.2
        self.batch_delay = 4.7
    
    def get_user_id(self):
        """Get your own user ID from the token"""
        try:
            r = requests.get(f'{self.base_url}/users/@me', headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                print(f"Authenticated as: {data.get('username')}#{data.get('discriminator', '0')}")
                return data['id']
            else:
                print(f"Authentication failed: HTTP {r.status_code}")
                if r.status_code == 401:
                    print("Invalid token provided")
                return None
        except Exception as e:
            print(f"Connection error: {e}")
            return None
    
    def get_channel_id_from_dm(self, user_id):
        """Open/create DM channel with user and return channel ID"""
        payload = {'recipient_id': user_id}
        try:
            r = requests.post(f'{self.base_url}/users/@me/channels', 
                           headers=self.headers, json=payload, timeout=10)
            if r.status_code == 200:
                return r.json()['id']
            elif r.status_code == 429:
                retry = r.json().get('retry_after', 5)
                print(f"Rate limited opening DM, waiting {retry}s...")
                time.sleep(retry)
                return self.get_channel_id_from_dm(user_id)
            else:
                print(f"Failed to open DM: HTTP {r.status_code}")
                return None
        except Exception as e:
            print(f"Error opening DM: {e}")
            return None
    
    def get_guild_channels(self, guild_id):
        """Get all text channels in a guild"""
        try:
            r = requests.get(f'{self.base_url}/guilds/{guild_id}/channels', 
                          headers=self.headers, timeout=10)
            if r.status_code == 200:
                channels = [c for c in r.json() if c['type'] == 0]
                print(f"Found {len(channels)} text channels")
                return channels
            elif r.status_code == 429:
                retry = r.json().get('retry_after', 5)
                print(f"Rate limited getting channels, waiting {retry}s...")
                time.sleep(retry)
                return self.get_guild_channels(guild_id)
            else:
                print(f"Failed to get channels: HTTP {r.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching channels: {e}")
            return []
    
    def fetch_messages(self, channel_id, user_id=None, limit=100, before=None):
        """Fetch messages from a channel with rate limit handling"""
        params = {'limit': limit}
        if before:
            params['before'] = before
        
        try:
            r = requests.get(f'{self.base_url}/channels/{channel_id}/messages',
                          headers=self.headers, params=params, timeout=10)
            
            if r.status_code == 200:
                messages = r.json()
                if user_id:
                    messages = [m for m in messages if m['author']['id'] == user_id]
                return messages
            elif r.status_code == 429:
                self.rate_limit_hits += 1
                retry_after = r.json().get('retry_after', 5)
                print(f"Rate limited on fetch (hit #{self.rate_limit_hits}), waiting {retry_after}s...")
                time.sleep(retry_after + 1)
                return self.fetch_messages(channel_id, user_id, limit, before)
            elif r.status_code == 403:
                print("No access to this channel, skipping...")
                return []
            else:
                print(f"Fetch error: HTTP {r.status_code}")
                return []
        except Exception as e:
            print(f"Network error fetching messages: {e}")
            time.sleep(3)
            return []
    
    def delete_message(self, channel_id, message_id):
        """Delete a specific message with strict rate limiting"""
        try:
            r = requests.delete(f'{self.base_url}/channels/{channel_id}/messages/{message_id}',
                              headers=self.headers, timeout=10)
            
            if r.status_code == 204:
                self.deleted_count += 1
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                return True
            elif r.status_code == 429:
                self.rate_limit_hits += 1
                retry_after = r.json().get('retry_after', 5)
                print(f"Rate limited on delete (hit #{self.rate_limit_hits}), backing off for {retry_after}s...")
                time.sleep(retry_after + 2)
                return self.delete_message(channel_id, message_id)
            elif r.status_code == 404:
                print("Message already deleted or not found")
                return True
            elif r.status_code == 403:
                print("No permission to delete this message")
                self.failed_count += 1
                return False
            else:
                print(f"Delete failed: HTTP {r.status_code}")
                self.failed_count += 1
                time.sleep(2)
                return False
        except Exception as e:
            print(f"Network error deleting: {e}")
            self.failed_count += 1
            time.sleep(3)
            return False
    
    def delete_from_dm(self, target_user_id, my_user_id):
        """Delete all your messages from a DM conversation"""
        print(f"\nOpening DM with user {target_user_id}...")
        channel_id = self.get_channel_id_from_dm(target_user_id)
        
        if not channel_id:
            print("Failed to open DM channel")
            return
        
        print(f"DM Channel opened: {channel_id}")
        print("Fetching messages (this may take a while)...")
        
        last_id = None
        total_checked = 0
        batch_num = 0
        
        while True:
            batch_num += 1
            messages = self.fetch_messages(channel_id, my_user_id, before=last_id)
            
            if not messages:
                print("No more messages found")
                break
            
            total_checked += len(messages)
            print(f"\nBatch {batch_num}: Found {len(messages)} of your messages to delete")
            
            for i, msg in enumerate(messages, 1):
                timestamp = msg['timestamp'][:19].replace('T', ' ')
                content = msg['content'][:60].replace('\n', ' ')
                if len(msg['content']) > 60:
                    content += "..."
                
                print(f"  [{i}/{len(messages)}] [{timestamp}] {content}")
                
                self.delete_message(channel_id, msg['id'])
                last_id = msg['id']
            
            print(f"Progress: {self.deleted_count} deleted, {self.failed_count} failed, {self.rate_limit_hits} rate limits")
            
            if len(messages) >= 100:
                print(f"Pausing {self.batch_delay}s between batches...")
                time.sleep(self.batch_delay)
            else:
                break
        
        print(f"\n{'='*60}")
        print(f"DM purge complete!")
        print(f"   Total deleted: {self.deleted_count}")
        print(f"   Failed: {self.failed_count}")
        print(f"   Rate limit hits: {self.rate_limit_hits}")
        print(f"{'='*60}")
    
    def delete_from_server(self, guild_id, my_user_id):
        """Delete all your messages from all channels in a server"""
        print(f"\nFetching channels from guild {guild_id}...")
        channels = self.get_guild_channels(guild_id)
        
        if not channels:
            print("No channels found or no access")
            return
        
        print(f"\nWill process {len(channels)} channels")
        print("Starting in 5 seconds... (Ctrl+C to cancel)")
        time.sleep(5)
        
        for idx, channel in enumerate(channels, 1):
            channel_name = channel['name']
            channel_id = channel['id']
            
            print(f"\n{'='*60}")
            print(f"Channel {idx}/{len(channels)}: #{channel_name}")
            print(f"{'='*60}")
            
            channel_deleted = 0
            last_id = None
            batch_num = 0
            
            while True:
                batch_num += 1
                messages = self.fetch_messages(channel_id, my_user_id, before=last_id)
                
                if not messages:
                    if batch_num == 1:
                        print("No messages found in this channel")
                    break
                
                print(f"Batch {batch_num}: {len(messages)} messages to delete")
                
                for msg in messages:
                    timestamp = msg['timestamp'][:19].replace('T', ' ')
                    content = msg['content'][:50].replace('\n', ' ')
                    if len(msg['content']) > 50:
                        content += "..."
                    
                    print(f"    [{timestamp}] {content}")
                    
                    if self.delete_message(channel_id, msg['id']):
                        channel_deleted += 1
                    
                    last_id = msg['id']
                
                print(f"    Channel progress: {channel_deleted} deleted")
                
                if len(messages) < 100:
                    break
                else:
                    print(f"    Pausing {self.batch_delay}s...")
                    time.sleep(self.batch_delay)
            
            print(f"Finished #{channel_name}: {channel_deleted} deleted")
            
            if idx < len(channels):
                print(f"  Waiting 10s before next channel...")
                time.sleep(10)
        
        print(f"\n{'='*60}")
        print(f"Server purge complete!")
        print(f"   Total deleted: {self.deleted_count}")
        print(f"   Failed: {self.failed_count}")
        print(f"   Rate limit hits: {self.rate_limit_hits}")
        print(f"{'='*60}")


def print_banner():
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║                    PurgeSelf v1.0.0                          ║
║          Discord Self-Message Purge Tool                     ║
║                                                              ║
║              Made by HolyVizle001 on GitHub                  ║
║            https://github.com/HolyVizle001                   ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    print_banner()
    
    print("\nWARNING: This tool uses self-bot automation")
    print("This violates Discord's Terms of Service")
    print("Your account may be BANNED")
    print("Only use on accounts you are willing to lose")
    print("Strict rate limiting is enabled (slow but safer)")
    print("\n" + "="*60)
    
    token = input("\nEnter your Discord user token: ").strip()
    if not token:
        print("No token provided, exiting")
        return
    
    deleter = DiscordMessageDeleter(token)
    
    print("\nVerifying token...")
    my_user_id = deleter.get_user_id()
    if not my_user_id:
        print("Failed to authenticate")
        return
    
    print("\nSelect mode:")
    print("  [1] Delete from DM (user ID)")
    print("  [2] Delete from Server (guild ID)")
    
    choice = input("\nChoice (1/2): ").strip()
    
    if choice == '1':
        target_id = input("Enter the USER ID to delete DMs with: ").strip()
        if not target_id.isdigit():
            print("Invalid user ID")
            return
        
        print(f"\nThis will delete ALL your messages in DMs with user {target_id}")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm == 'DELETE':
            try:
                deleter.delete_from_dm(target_id, my_user_id)
            except KeyboardInterrupt:
                print(f"\n\nInterrupted! Deleted {deleter.deleted_count} messages before stopping.")
        else:
            print("Cancelled")
    
    elif choice == '2':
        guild_id = input("Enter the GUILD ID (server ID): ").strip()
        if not guild_id.isdigit():
            print("Invalid guild ID")
            return
        
        print(f"\nThis will delete ALL your messages in ALL channels of server {guild_id}")
        print("This could take a very long time")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm == 'DELETE':
            try:
                deleter.delete_from_server(guild_id, my_user_id)
            except KeyboardInterrupt:
                print(f"\n\nInterrupted! Deleted {deleter.deleted_count} messages before stopping.")
        else:
            print("Cancelled")
    
    else:
        print("Invalid choice")
    
    print(f"\nMade by HolyVizle001 on GitHub")
    print("Thanks for using PurgeSelf!")


if __name__ == '__main__':
    main()
