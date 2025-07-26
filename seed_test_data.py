"""
Create test data for Discord Curator Monitoring System
This will populate the database with sample curators, activities, and servers
"""

from app import app, db
from models import *
from datetime import datetime, timedelta
import json
import random

def seed_test_data():
    """Create test data for all major components"""
    with app.app_context():
        print("🌱 Seeding test data...")
        
        # Create test Discord servers
        servers_data = [
            {'discord_id': '123456789001', 'name': 'Government', 'is_active': True},
            {'discord_id': '123456789002', 'name': 'FIB', 'is_active': True},
            {'discord_id': '123456789003', 'name': 'LSPD', 'is_active': True},
            {'discord_id': '123456789004', 'name': 'SANG', 'is_active': True},
            {'discord_id': '123456789005', 'name': 'LSCSD', 'is_active': True},
            {'discord_id': '123456789006', 'name': 'EMS', 'is_active': True},
            {'discord_id': '123456789007', 'name': 'Weazel News', 'is_active': True},
            {'discord_id': '123456789008', 'name': 'Detectives', 'is_active': True}
        ]
        
        servers = []
        for server_data in servers_data:
            server = DiscordServers.query.filter_by(discord_id=server_data['discord_id']).first()
            if not server:
                server = DiscordServers()
                server.discord_id = server_data['discord_id']
                server.name = server_data['name']
                server.is_active = server_data['is_active']
                db.session.add(server)
                servers.append(server)
        
        db.session.commit()
        print(f"✅ Created {len(servers_data)} Discord servers")
        
        # Create test curators
        curators_data = [
            {'name': 'Алексей Волков', 'discord_id': '111111111111', 'factions': ['Government'], 'curator_type': 'Главный куратор'},
            {'name': 'Мария Петрова', 'discord_id': '222222222222', 'factions': ['FIB'], 'curator_type': 'Куратор'},
            {'name': 'Иван Сидоров', 'discord_id': '333333333333', 'factions': ['LSPD'], 'curator_type': 'Куратор'},
            {'name': 'Елена Козлова', 'discord_id': '444444444444', 'factions': ['SANG'], 'curator_type': 'Куратор'},
            {'name': 'Дмитрий Морозов', 'discord_id': '555555555555', 'factions': ['EMS'], 'curator_type': 'Куратор'},
            {'name': 'Анна Белова', 'discord_id': '666666666666', 'factions': ['Weazel News'], 'curator_type': 'Куратор'},
            {'name': 'Павел Орлов', 'discord_id': '777777777777', 'factions': ['LSCSD'], 'curator_type': 'Куратор'},
            {'name': 'Ольга Новикова', 'discord_id': '888888888888', 'factions': ['Detectives'], 'curator_type': 'Куратор'}
        ]
        
        curators = []
        for curator_data in curators_data:
            curator = Curators.query.filter_by(discord_id=curator_data['discord_id']).first()
            if not curator:
                curator = Curators()
                curator.name = curator_data['name']
                curator.discord_id = curator_data['discord_id']
                curator.factions = json.dumps(curator_data['factions'])
                curator.curator_type = curator_data['curator_type']
                curator.is_active = True
                db.session.add(curator)
                curators.append(curator)
        
        db.session.commit()
        print(f"✅ Created {len(curators_data)} test curators")
        
        # Create test activities
        all_servers = DiscordServers.query.all()
        all_curators = Curators.query.all()
        
        activity_types = ['message', 'reaction', 'reply']
        channels = ['general', 'help-desk', 'announcements', 'reports', 'discussions']
        
        activities_created = 0
        for i in range(100):  # Create 100 test activities
            activity = Activities()
            activity.curator_id = random.choice(all_curators).id
            activity.server_id = random.choice(all_servers).id
            activity.type = random.choice(activity_types)
            activity.channel_name = random.choice(channels)
            activity.content = f"Тестовое {activity.type} #{i+1}"
            activity.timestamp = datetime.now() - timedelta(hours=random.randint(0, 72))
            
            if activity.type == 'reaction':
                activity.reaction_emoji = random.choice(['👍', '❤️', '😊', '✅', '👏'])
            
            db.session.add(activity)
            activities_created += 1
        
        db.session.commit()
        print(f"✅ Created {activities_created} test activities")
        
        # Create test response tracking
        responses_created = 0
        for i in range(30):  # Create 30 response tracking entries
            response = ResponseTracking()
            response.curator_id = random.choice(all_curators).id
            response.server_id = random.choice(all_servers).id
            response.channel_name = random.choice(channels)
            response.help_message_content = f"Помогите с вопросом #{i+1}"
            response.help_timestamp = datetime.now() - timedelta(hours=random.randint(1, 48))
            
            # Some responses have been answered
            if random.choice([True, False, True]):  # 2/3 chance of being answered
                response.response_timestamp = response.help_timestamp + timedelta(minutes=random.randint(1, 30))
                response.response_time_seconds = int((response.response_timestamp - response.help_timestamp).total_seconds())
                response.response_content = f"Ответ на вопрос #{i+1}"
            
            db.session.add(response)
            responses_created += 1
        
        db.session.commit()
        print(f"✅ Created {responses_created} response tracking entries")
        
        print("🎉 Test data seeding completed!")

if __name__ == "__main__":
    seed_test_data()