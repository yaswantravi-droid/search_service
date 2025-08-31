#!/usr/bin/env python3
"""
Test Available Atlas Search Commands
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_atlas_commands():
    """Test what Atlas Search commands are available."""
    
    mongodb_url = os.getenv("MONGODB_URL")
    print(f"Testing Atlas Search commands with: {mongodb_url}")
    
    try:
        client = AsyncIOMotorClient(mongodb_url)
        db = client.get_database()
        
        print("✅ Connected to MongoDB Atlas")
        
        # Test 1: Try to list all available commands
        print("\n🔍 Test 1: List available commands")
        try:
            # Try to get command list
            result = await db.command("listCommands")
            print("✅ listCommands works")
            commands = result.get("commands", [])
            atlas_commands = [cmd for cmd in commands if "search" in cmd.get("help", "").lower()]
            print(f"   Atlas Search related commands: {atlas_commands}")
        except Exception as e:
            print(f"❌ listCommands failed: {e}")
        
        # Test 2: Try different variations of search index commands
        print("\n🔍 Test 2: Try different search index command variations")
        
        commands_to_try = [
            ("listSearchIndexes", "bots"),
            ("listSearchIndexes", "interactly.bots"),
            ("listSearchIndexes", "interactly", "bots"),
            ("searchIndexes", "bots"),
            ("search.indexes", "bots"),
            ("atlasSearchIndexes", "bots"),
        ]
        
        for cmd, *args in commands_to_try:
            try:
                if len(args) == 1:
                    result = await db.command(cmd, args[0])
                else:
                    result = await db.command(cmd, *args)
                print(f"✅ {cmd} works with args {args}")
                print(f"   Result: {result}")
                break
            except Exception as e:
                print(f"❌ {cmd} failed with args {args}: {e}")
        
        # Test 3: Try to get database info to understand cluster type
        print("\n🔍 Test 3: Get database and cluster info")
        try:
            # Try to get build info
            build_info = await db.command("buildInfo")
            print("✅ buildInfo works")
            print(f"   Version: {build_info.get('version', 'N/A')}")
            print(f"   Git version: {build_info.get('gitVersion', 'N/A')}")
        except Exception as e:
            print(f"❌ buildInfo failed: {e}")
        
        try:
            # Try to get host info
            host_info = await db.command("hostInfo")
            print("✅ hostInfo works")
            print(f"   OS: {host_info.get('os', {}).get('name', 'N/A')}")
        except Exception as e:
            print(f"❌ hostInfo failed: {e}")
        
        # Test 4: Try to access existing search index directly
        print("\n🔍 Test 4: Try to use existing search index")
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "bots_name_index_1",
                        "text": {
                            "query": "test",
                            "path": "name"
                        }
                    }
                },
                {"$limit": 1}
            ]
            
            result = await db.bots.aggregate(pipeline).to_list(1)
            print(f"✅ Atlas Search query works! Found {len(result)} results")
            
        except Exception as e:
            print(f"❌ Atlas Search query failed: {e}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Testing Available Atlas Search Commands")
    print("=" * 50)
    
    asyncio.run(test_atlas_commands())
