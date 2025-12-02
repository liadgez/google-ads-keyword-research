"""
WhatsApp Message Handler
Processes incoming WhatsApp messages and routes them to appropriate handlers
"""

import os
import re
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from whatsapp_client import WhatsAppClient
from competitor_research import CompetitorResearcher
from keyword_planner import generate_keyword_ideas
from clustering import ClusteringEngine
from sheets_exporter_clustered import create_and_export_clustered
from sheets_exporter_competitor import create_and_export_competitor_analysis

load_dotenv()

class WhatsAppHandler:
    """Handles incoming WhatsApp messages and processes commands"""
    
    def __init__(self):
        self.client = WhatsAppClient()
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "myverifycode123")
        
        # Store active sessions (in production, use Redis or database)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription
        
        Args:
            mode: Should be "subscribe"
            token: Verification token from Meta
            challenge: Challenge string to return
            
        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            print("✅ Webhook verified successfully!")
            return challenge
        else:
            print("❌ Webhook verification failed")
            return None
    
    async def handle_message(self, message_data: Dict[str, Any]) -> None:
        """
        Process incoming WhatsApp message
        
        Args:
            message_data: Message data from webhook
        """
        try:
            # Extract message details
            from_number = message_data.get("from")
            message_id = message_data.get("id")
            message_type = message_data.get("type")
            
            # Mark as read
            await self.client.mark_as_read(message_id)
            
            # Handle different message types
            if message_type == "text":
                text_body = message_data.get("text", {}).get("body", "").strip()
                await self._handle_text_message(from_number, text_body, message_id)
            
            elif message_type == "interactive":
                # Handle button/list responses
                button_reply = message_data.get("interactive", {})
                if button_reply.get("type") == "button_reply":
                    button_id = button_reply.get("button_reply", {}).get("id")
                    await self._handle_button_response(from_number, button_id)
            
            else:
                # Unsupported message type
                await self.client.send_text_message(
                    from_number,
                    "Sorry, I can only process text messages right now. 📝"
                )
        
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            # Send error message to user
            try:
                await self.client.send_text_message(
                    from_number,
                    "⚠️ Oops! Something went wrong. Please try again or type 'help' for assistance."
                )
            except:
                pass
    
    async def _handle_text_message(self, from_number: str, text: str, message_id: str) -> None:
        """Handle text message commands"""
        
        # Save user as the latest subscriber for hourly updates
        try:
            with open("last_user.txt", "w") as f:
                f.write(from_number)
        except Exception as e:
            print(f"Error saving user: {e}")
        
        text_lower = text.lower().strip()
        
        # Handle numbered menu responses
        if text_lower in ["1", "1️⃣"]:
            await self.client.send_text_message(
                from_number,
                "🔍 *Keyword Research*\n\nSend me a URL to analyze:\n\nExample:\n`research https://example.com`"
            )
            return
        elif text_lower in ["2", "2️⃣"]:
            await self.client.send_text_message(
                from_number,
                "🕵️ *Competitor Analysis*\n\nSend me a URL to analyze:\n\nExample:\n`competitors https://example.com`"
            )
            return
        
        # Help command
        if text_lower in ["help", "start", "hi", "hello", "menu"]:
            await self._send_help_message(from_number)
            return
        
        # Status command
        if text_lower in ["status", "ping"]:
            await self.client.send_reaction(from_number, message_id, "✅")
            await self.client.send_text_message(
                from_number,
                "🟢 Bot is online and ready!\n\nType 'help' to see available commands."
            )
            return
        
        # Extract URL from message
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        urls = re.findall(url_pattern, text)
        
        if not urls:
            await self.client.send_text_message(
                from_number,
                "❌ Please include a valid URL in your message.\n\nExample:\n• research https://netflix.com\n• competitors https://netflix.com"
            )
            return
        
        url = urls[0]
        
        # Determine command type
        if any(keyword in text_lower for keyword in ["research", "keyword", "keywords", "kw"]):
            await self._handle_keyword_research(from_number, url, message_id)
        
        elif any(keyword in text_lower for keyword in ["competitor", "competitors", "comp", "analyze"]):
            await self._handle_competitor_research(from_number, url, message_id)
        
        else:
            # Ask user what they want to do
            await self.client.send_interactive_buttons(
                to=from_number,
                body_text=f"What would you like to do with:\n{url}",
                buttons=[
                    {"id": f"kw_{url}", "title": "🔍 Keyword Research"},
                    {"id": f"comp_{url}", "title": "🕵️ Competitor Analysis"}
                ],
                footer_text="Choose an option"
            )
    
    async def _handle_button_response(self, from_number: str, button_id: str) -> None:
        """Handle interactive button responses"""
        
        if button_id.startswith("kw_"):
            url = button_id[3:]
            await self._handle_keyword_research(from_number, url, None)
        
        elif button_id.startswith("comp_"):
            url = button_id[5:]
            await self._handle_competitor_research(from_number, url, None)
        
        elif button_id == "btn_research":
            await self.client.send_text_message(
                from_number,
                "🔍 *Keyword Research*\n\nSend me a URL to analyze:\n\nExample:\n`research https://example.com`"
            )
        
        elif button_id == "btn_competitors":
            await self.client.send_text_message(
                from_number,
                "🕵️ *Competitor Analysis*\n\nSend me a URL to analyze:\n\nExample:\n`competitors https://example.com`"
            )
    
    async def _handle_keyword_research(self, from_number: str, url: str, message_id: Optional[str]) -> None:
        """Process keyword research request"""
        
        # Send acknowledgment
        if message_id:
            await self.client.send_reaction(from_number, message_id, "🔍")
        
        await self.client.send_text_message(
            from_number,
            "🔍 *Keyword Research Started*\n\n"
            f"Analyzing: {url}\n\n"
            "⏳ This may take 30-60 seconds...\n"
            "I'll send you the results shortly!"
        )
        
        try:
            # Fetch keywords
            result = generate_keyword_ideas(url)
            
            if not result.get('success'):
                await self.client.send_text_message(
                    from_number,
                    f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                    "Please check the URL and try again."
                )
                return
            
            keywords = result.get('keywords', [])
            
            if not keywords:
                await self.client.send_text_message(
                    from_number,
                    "⚠️ No keywords found for this URL.\n\n"
                    "Try a different website or check if the URL is accessible."
                )
                return
            
            # Cluster keywords (using hybrid method)
            engine = ClusteringEngine()
            clusters = engine.cluster_hybrid(keywords)
            
            # Export to Google Sheets
            sheet_url = create_and_export_clustered(clusters, url)
            
            # Calculate stats
            total_keywords = len(keywords)
            total_clusters = len(clusters)
            total_volume = sum(k.get('avgMonthlySearches', 0) for k in keywords)
            
            # Get negative keywords count
            negative_count = len(clusters[0].negative_candidates) if clusters and clusters[0].negative_candidates else 0
            
            # Send results
            result_message = (
                "✅ *Keyword Research Complete!*\n\n"
                f"📊 *Results Summary:*\n"
                f"• Keywords Found: {total_keywords:,}\n"
                f"• Ad Groups Created: {total_clusters}\n"
                f"• Total Search Volume: {total_volume:,}/month\n"
                f"• Negative Keywords: {negative_count}\n\n"
            )
            
            if sheet_url:
                result_message += (
                    f"📈 *View Full Report:*\n{sheet_url}\n\n"
                    "The sheet includes:\n"
                    "✓ All keywords with metrics\n"
                    "✓ Clustered ad groups\n"
                    "✓ Pivot table overview\n"
                    "✓ Negative keywords list"
                )
            else:
                result_message += "⚠️ Google Sheets export failed, but analysis completed successfully."
            
            await self.client.send_text_message(from_number, result_message)
            
            # Send top 3 ad groups as preview
            if clusters:
                preview_message = "\n📋 *Top 3 Ad Groups:*\n\n"
                for i, cluster in enumerate(clusters[:3], 1):
                    kw_preview = ", ".join([k['keyword'] for k in cluster.keywords[:3]])
                    vol = sum(k.get('avgMonthlySearches', 0) for k in cluster.keywords)
                    preview_message += f"{i}. *{cluster.name}*\n"
                    preview_message += f"   Keywords: {kw_preview}...\n"
                    preview_message += f"   Volume: {vol:,}/mo\n\n"
                
                await self.client.send_text_message(from_number, preview_message)
        
        except Exception as e:
            print(f"❌ Keyword research error: {e}")
            await self.client.send_text_message(
                from_number,
                f"❌ *Error during keyword research*\n\n"
                f"Details: {str(e)}\n\n"
                "Please try again or contact support."
            )
    
    async def _handle_competitor_research(self, from_number: str, url: str, message_id: Optional[str]) -> None:
        """Process competitor research request"""
        
        # Send acknowledgment
        if message_id:
            await self.client.send_reaction(from_number, message_id, "🕵️")
        
        await self.client.send_text_message(
            from_number,
            "🕵️ *Competitor Analysis Started*\n\n"
            f"Analyzing: {url}\n\n"
            "⏳ This may take 30-60 seconds...\n"
            "Using AI to find competitors and market insights!"
        )
        
        try:
            # Run competitor analysis
            researcher = CompetitorResearcher()
            result = await researcher.analyze(url, method='gemini')
            
            # Export to Google Sheets
            sheet_url = create_and_export_competitor_analysis(result)
            
            # Send results
            result_message = (
                "✅ *Competitor Analysis Complete!*\n\n"
                f"🏢 *Brand:* {result.brand_info.brandName}\n"
                f"🔑 *Main Keyword:* {result.selected_keyword}\n"
                f"🎯 *Competitors Found:* {len(result.competitors)}\n\n"
            )
            
            if result.market_insight:
                insight_preview = result.market_insight[:200] + "..." if len(result.market_insight) > 200 else result.market_insight
                result_message += f"💡 *Market Insight:*\n{insight_preview}\n\n"
            
            if sheet_url:
                result_message += f"📊 *Full Report:*\n{sheet_url}"
            
            await self.client.send_text_message(from_number, result_message)
            
            # Send top competitors
            if result.competitors:
                comp_message = "\n🏆 *Top Competitors:*\n\n"
                for i, comp in enumerate(result.competitors[:5], 1):
                    comp_message += f"{i}. *{comp.name}*\n"
                    comp_message += f"   🌐 {comp.domain}\n"
                    comp_message += f"   📊 Confidence: {comp.confidence}%\n"
                    comp_message += f"   📝 {comp.description[:80]}...\n\n"
                
                await self.client.send_text_message(from_number, comp_message)
        
        except Exception as e:
            print(f"❌ Competitor research error: {e}")
            await self.client.send_text_message(
                from_number,
                f"❌ *Error during competitor analysis*\n\n"
                f"Details: {str(e)}\n\n"
                "Please try again or contact support."
            )
    
    async def _send_help_message(self, from_number: str) -> None:
        """Send help/welcome message with interactive buttons"""
        
        help_text = (
            "👋 *Welcome to Google Ads Research Bot!*\n\n"
            "I can help you with:\n\n"
            "*1️⃣ Keyword Research*\n"
            "Find thousands of keywords, cluster them into ad groups, and get Google Sheets reports.\n\n"
            "*2️⃣ Competitor Analysis*\n"
            "Discover your competitors and get AI-powered market insights.\n\n"
            "*Reply with:*\n"
            "• Number (1 or 2) to choose\n"
            "• Or type your command directly:\n"
            "  - `research https://example.com`\n"
            "  - `competitors https://example.com`\n\n"
            "Ready to start? 🚀"
        )
        
        try:
            # Try to send interactive buttons
            await self.client.send_interactive_buttons(
                to=from_number,
                body_text=help_text,
                buttons=[
                    {"id": "btn_research", "title": "🔍 Keyword Research"},
                    {"id": "btn_competitors", "title": "🕵️ Competitors"}
                ],
                footer_text="Choose an option or reply with 1 or 2"
            )
        except Exception as e:
            # Fallback to plain text if buttons fail
            print(f"Failed to send buttons, using plain text: {e}")
            await self.client.send_text_message(from_number, help_text)

