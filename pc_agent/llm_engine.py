"""
LLM Engine - OpenAI GPT for conversation and analysis
Best quality for telecalling
"""
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, SYSTEM_PROMPT, logger


class LLMEngine:
    def __init__(self):
        # OPENAI CLIENT (Best Quality)
        if not OPENAI_API_KEY:
            logger.error("❌ OpenAI API key not set!")
            raise ValueError("OpenAI API key required")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        
        self.conversation_history = []
        logger.info(f"🤖 LLM Engine ready | Model: {self.model}")
    
    def reset_conversation(self):
        """Reset for new call"""
        self.conversation_history = []
        logger.debug("Conversation reset")
    
    def generate_response(self, user_text):
        """Generate short but COMPLETE Hindi response"""
        try:
            self.conversation_history.append({"role": "user", "content": user_text})
            
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            full_reply = response.choices[0].message.content.strip()
            full_reply = ' '.join(full_reply.split())
            
            self.conversation_history.append({"role": "assistant", "content": full_reply})
            
            logger.debug(f"AI Response: {full_reply}")
            return full_reply
        
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "Ji, ek second. Dobara boliye?"
    
    def generate_response_streaming(self, user_text):
        """Generate response with STREAMING - yields sentences as they come"""
        try:
            self.conversation_history.append({"role": "user", "content": user_text})
            
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                stream=True
            )
            
            full_reply = ""
            sentence_buffer = ""
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_reply += text
                    sentence_buffer += text
                    
                    # Yield sentence when complete
                    if any(p in text for p in ['.', '!', '?', '।', '\n']):
                        if sentence_buffer.strip():
                            yield sentence_buffer.strip()
                            sentence_buffer = ""
            
            # Yield remaining
            if sentence_buffer.strip():
                yield sentence_buffer.strip()
            
            full_reply = full_reply.strip()
            full_reply = ' '.join(full_reply.split())
            
            self.conversation_history.append({"role": "assistant", "content": full_reply})
            
            logger.debug(f"AI Response: {full_reply}")
        
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield "Ji, ek second. Dobara boliye?"

    
    def analyze_conversation(self):
        """Analyze call and return result"""
        if not self.conversation_history:
            return {
                "interest": "NO_CONVERSATION",
                "result": "NO_RESPONSE", 
                "summary": "Koi baat nahi hui"
            }
        
        try:
            conversation_text = self.get_conversation_text()
            
            prompt = f"""Ye call conversation analyze karo:

{conversation_text}

Batao (Hindi me):
1. INTEREST: INTERESTED / NOT_INTERESTED / NEUTRAL
2. RESULT: POSITIVE / NEGATIVE / CUT / NO_RESPONSE  
3. SUMMARY: 1 line summary

Format:
INTEREST: <value>
RESULT: <value>
SUMMARY: <summary>"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            return self._parse_analysis(response.choices[0].message.content)
        
        except Exception as e:
            logger.error(f"Analysis Error: {e}")
            return {"interest": "ERROR", "result": "ERROR", "summary": str(e)}
    
    def get_conversation_text(self):
        """Get conversation as text"""
        lines = []
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)
    
    def _parse_analysis(self, text):
        """Parse analysis response"""
        result = {"interest": "UNKNOWN", "result": "UNKNOWN", "summary": ""}
        
        for line in text.strip().split("\n"):
            line = line.strip().upper()
            if line.startswith("INTEREST:"):
                val = line.split(":", 1)[1].strip()
                if "NOT" in val:
                    result["interest"] = "NOT_INTERESTED"
                elif "INTERESTED" in val:
                    result["interest"] = "INTERESTED"
                else:
                    result["interest"] = "NEUTRAL"
            
            elif line.startswith("RESULT:"):
                val = line.split(":", 1)[1].strip()
                for r in ["POSITIVE", "NEGATIVE", "CUT", "NO_RESPONSE"]:
                    if r in val:
                        result["result"] = r
                        break
            
            elif line.startswith("SUMMARY:"):
                result["summary"] = text.split("SUMMARY:", 1)[1].strip().split("\n")[0]
        
        return result


if __name__ == "__main__":
    print("Testing LLM Engine...")
    llm = LLMEngine()
    
    response = llm.generate_response("Ye course kitne din ka hai?")
    print(f"Response: {response}")
    
    response = llm.generate_response("Fees kitni hai?")
    print(f"Response: {response}")
    
    analysis = llm.analyze_conversation()
    print(f"Analysis: {analysis}")
