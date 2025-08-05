# app/scripts/generate_fake_data.py
import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
import json
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
import traceback

# 导入实体模型
from app.entities.user_entity import User
from app.entities.post_entity import Post
from app.entities.comment_entity import Comment
from app.entities.like_entity import Like
from app.entities.favorite_entity import Favorite
from app.entities.chase_entity import Chase
from app.entities.follow_entity import Follow
from app.entities.push_entity import Push
from app.entities.notification_entity import Notification
from app.core.config import settings

# 导入服务和模式
from app.features.user.user_service import UserService
from app.schemas.user_schema import UserBase, UserFilter, PaginationParams
from app.features.agent.agent_service import AgentService
from app.schemas.agent_schema import AgentCreate, AgentFilter
from app.features.like.like_service import LikeService
from app.schemas.like_schema import LikeCreate
from app.features.favorite.favorite_service import FavoriteService
from app.schemas.favorite_schema import FavoriteCreate
from app.features.chase.chase_service import ChaseService
from app.schemas.chase_schema import ChaseCreate
from app.features.follow.follow_service import FollowService
from app.schemas.follow_schema import FollowCreate
from app.features.comment.comment_service import CommentService
from app.schemas.comment_schema import CommentCreate
from app.schemas.post_schema import PostCreate
from app.entities.agent_entity import Agent
# 初始化Faker
fake = Faker('en_US') 
# 配置参数
NUM_USERS = 3  # 用户数量
NUM_AGENTS = 2  # AI代理数量
NUM_POSTS = 10  # 帖子数量
NUM_COMMENTS = 15  # 评论数量
NUM_LIKES = 20  # 点赞数量
NUM_FAVORITES = 8  # 收藏数量
NUM_CHASES = 12  # 关注代理数量
NUM_FOLLOWS = 8  # 关注用户数量
NUM_PUSHES = 10  # 推送数量
NUM_NOTIFICATIONS = 15  # 通知数量
BASE_DATE = datetime.utcnow() - timedelta(days=30)  # 从30天前开始

# 存储生成的数据ID
posts_ids = []
comments_ids = []

# 帮助函数：生成随机日期
def random_date(start_date=BASE_DATE):
    return start_date + timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

# 创建用户数据
async def create_users():
    print("开始创建用户数据...")
    created_users = []
    for i in range(NUM_USERS):
        name = fake.name()
        email = fake.email()
        phone = fake.phone_number()
        
        user = UserBase(
            name=name,
            email=email,
            phone=phone,
            password=fake.password(),
            picture=fake.image_url(),
            bio=fake.text(max_nb_chars=200),
            metadata={
                "auth0_user_id": f"auth0|{uuid4().hex[:24]}",
                "last_login": random_date().isoformat(),
                "login_count": random.randint(1, 50),
                "preferences": {
                    "theme": random.choice(["light", "dark", "system"]),
                    "notifications": random.choice([True, False])
                }
            }
        )
        # 使用Service创建用户并获取创建的用户
        created_user = await UserService.create_user(user)
        created_users.append(created_user)
    
    print(f"创建了 {len(created_users)} 个用户")
    return created_users

# 创建AI代理数据
async def create_agents(users):
    print("开始创建AI代理数据...")
    created_agents = []
    for i in range(NUM_AGENTS):
        # 随机选择一个用户作为代理拥有者
        print(users)
        user = random.choice(users)
        print(user)
        agent = AgentCreate(
            agent_name=fake.name(),
            avatar=fake.image_url(),
            accuracy_score=random.uniform(0, 100),
            visibility=random.choice(["public", "private"]),
            description=fake.text(max_nb_chars=200),
            user_id=user.id,
            tags=fake.words(nb=random.randint(1, 3))
        )
        created_agent = await AgentService.create_agent(agent)
        created_agents.append(created_agent)
    
    print(f"创建了 {len(created_agents)} 个AI代理")
    return created_agents

# 创建帖子数据
async def create_posts(agents):
    print("开始创建帖子数据...")
    created_posts = []
    for i in range(NUM_POSTS):
        try:
            # 随机选择一个代理作为作者
            agent = random.choice(agents)
            
            # 创建当前时间 - 随机日期作为帖子时间
            post_date = random_date()
            
            # 生成随机媒体URL列表
            media_urls = {fake.file_name():fake.image_url() for _ in range(random.randint(0, 3))}
            
            # 生成随机标签
            tags = [fake.word() for _ in range(random.randint(1, 5))]
            
            # 随机可见性
            visibility = random.choice(["public", "private", "followers"])
            
            # 根据新的 contentData 结构
            content_data = {
                "title": fake.sentence(),
                "post_content": fake.text(max_nb_chars=500),
                "sources": [{"url": fake.uri(), "title": fake.sentence()} for _ in range(random.randint(0, 3))],
                "summary": fake.text(max_nb_chars=200)
            }
            
            # 创建帖子实体
            post = Post(
                agent_id=agent.id,
                card_type=random.choice(["text", "image", "video", "link"]),
                share_link=fake.uri(),
                content_data=content_data,
                media_urls=media_urls,
                tags=tags,
                date_time=post_date,
                published=random.choice([True, False]),
                visibility=visibility,
                status=random.choice(["draft", "published", "archived"]),
                trending_score=random.uniform(90, 100),
                created_at=post_date,
                updated_at=post_date + timedelta(hours=random.randint(0, 48))
            )
            
            post = await post.insert()
            posts_ids.append(str(post.id))
            created_posts.append(post)
        except Exception as e:
            print(f"创建帖子失败: {str(e)}")
            traceback.print_exc()
    
    print(f"创建了 {len(created_posts)} 个帖子")
    return created_posts

# 创建评论数据
async def create_comments(users, posts):
    print("开始创建评论数据...")
    created_comments = []
    
    for i in range(NUM_COMMENTS):
        try:
            # 随机选择一个用户作为评论者
            user = random.choice(users)
            # 随机选择一个帖子
            post = random.choice(posts)
            
            # 有25%的概率是对其他评论的回复
            is_reply = random.random() < 0.25 and created_comments
            
            # 确定目标类型和ID
            target_type = "comment" if is_reply else "post"
            target_id = str(random.choice(created_comments).id) if is_reply else str(post.id)
            
            # 创建评论数据
            comment_data = CommentCreate(
                user_id=user.id,
                target_id=target_id,  # 确保是字符串
                target_type=target_type,
                content=fake.paragraph(),
                has_children=False  # 如果是回复，设置parentId
            )
            
            # 使用Service创建评论
            created_comment = await CommentService.create_comment(comment_data)
            created_comments.append(created_comment)
            comments_ids.append(str(created_comment.id))
        except Exception as e:
            print(f"创建评论失败: {str(e)}")
    
    print(f"创建了 {len(created_comments)} 个评论")
    return created_comments

# 创建点赞数据
async def create_likes(users, posts, comments):
    print("开始创建点赞数据...")
    created_likes = []
    # 用于跟踪已创建的点赞组合，避免重复
    created_combos = set()
    
    for _ in range(NUM_LIKES):
        try:
            # 随机选择一个用户
            user = random.choice(users)
            
            # 随机选择目标类型
            target_type = random.choice(["post", "comment"])
            
            # 根据目标类型选择目标ID
            target = random.choice(posts if target_type == "post" else comments)
            target_id = str(target.id)
            
            # 检查这个组合是否已存在
            combo = (user.id, target_id, target_type)
            if combo in created_combos:
                continue
            
            created_combos.add(combo)
            
            # 创建点赞数据
            like_data = LikeCreate(
                user_id=user.id,
                target_id=target_id,
                target_type=target_type
            )
            
            # 使用Service创建点赞
            created_like = await LikeService.create_like(like_data)
            created_likes.append(created_like)
        except Exception as e:
            print(f"创建点赞失败: {str(e)}")
    
    print(f"创建了 {len(created_likes)} 个点赞")
    return created_likes

# 创建收藏数据
async def create_favorites(users, posts):
    print("开始创建收藏数据...")
    created_favorites = []
    # 用于跟踪已创建的收藏组合，避免重复
    created_combos = set()
    
    for _ in range(NUM_FAVORITES):
        try:
            # 随机选择一个用户
            user = random.choice(users)
            
            # 对于收藏，我们主要关注帖子
            target_type = "post"
            target = random.choice(posts)
            target_id = str(target.id)
            
            # 检查这个组合是否已存在
            combo = (user.id, target_id, target_type)
            if combo in created_combos:
                continue
            
            created_combos.add(combo)
            
            # 创建收藏数据
            favorite_data = FavoriteCreate(
                user_id=user.id,
                target_id=target_id,
                target_type=target_type
            )
            
            # 使用Service创建收藏
            created_favorite = await FavoriteService.create_favorite(favorite_data)
            created_favorites.append(created_favorite)
        except Exception as e:
            print(f"创建收藏失败: {str(e)}")
    
    print(f"创建了 {len(created_favorites)} 个收藏")
    return created_favorites

# 创建关注代理数据
async def create_chases(users, agents):
    print("开始创建关注代理数据...")
    created_chases = []
    # 用于跟踪已创建的关注组合，避免重复
    created_combos = set()
    
    for _ in range(NUM_CHASES):
        try:
            # 随机选择一个用户
            user = random.choice(users)
            
            # 随机选择一个代理
            agent = random.choice(agents)
            
            # 检查这个组合是否已存在
            combo = (user.id, agent.id)
            if combo in created_combos:
                continue
            
            created_combos.add(combo)
            
            # 创建关注数据
            chase_data = ChaseCreate(
                user_id=user.id,
                agent_id=agent.id,
                status="active",
                noti_freq=random.choice(["daily", "weekly", "monthly"]),
                noti_method=random.choice([["push"], ["email"], ["push", "email"]])
            )
            
            # 使用Service创建关注
            created_chase = await ChaseService.create_chase(chase_data)
            created_chases.append(created_chase)
        except Exception as e:
            print(f"创建代理关注失败: {str(e)}")
    
    print(f"创建了 {len(created_chases)} 个代理关注")
    return created_chases

# 创建关注用户数据 (Agent关注)
async def create_follows(users, agents):
    print("开始创建用户关注数据...")
    created_follows = []
    # 用于跟踪已创建的关注组合，避免重复
    created_combos = set()
    
    for _ in range(NUM_FOLLOWS):
        try:
            # 随机选择一个用户
            user = random.choice(users)
            
            # 随机选择一个代理
            agent = random.choice(agents)
            
            # 检查这个组合是否已存在
            combo = (user.id, agent.id)
            if combo in created_combos:
                continue
            
            created_combos.add(combo)
            
            # 创建关注数据
            follow_data = FollowCreate(
                user_id=user.id,
                agent_id=agent.id,
                status="active"
            )
            
            # 使用Service创建关注
            created_follow = await FollowService.create_follow(follow_data)
            created_follows.append(created_follow)
        except Exception as e:
            print(f"创建用户关注失败: {str(e)}")
    
    print(f"创建了 {len(created_follows)} 个用户关注")
    return created_follows

# 创建推送数据
async def create_pushes(users, posts):
    print("开始创建推送数据...")
    pushes = []
    
    for _ in range(NUM_PUSHES):
        try:
            # 随机选择一个用户作为接收者
            user = random.choice(users)
            
            # 随机选择一个帖子
            post = random.choice(posts)
            
            # 随机选择一个对象ID（可能是评论ID或其他）
            object_id = random.choice([str(post.id)] + comments_ids)
            
            # 推送时间
            pushed_at = random_date()
            
            push = Push(
                user_id=user.id,
                post_id=str(post.id),
                object_id=object_id,
                status=random.choice(["unread", "read", "unread"]),  # 大多数是未读的
                content=fake.sentence(),
                pushed_at=pushed_at,
                created_at=pushed_at,
                updated_at=pushed_at,
                metadata={
                    "action": random.choice(["comment", "like", "mention", "update"]),
                    "sender_id": random.choice(users).id
                }
            )
            await push.insert()
            pushes.append(push)
        except Exception as e:
            print(f"创建推送失败: {str(e)}")
    
    print(f"创建了 {len(pushes)} 个推送")
    return pushes

# 创建通知数据
async def create_notifications(users, posts, comments):
    print("开始创建通知数据...")
    notifications = []
    
    for _ in range(NUM_NOTIFICATIONS):
        try:
            # 随机选择一个用户作为接收者
            user = random.choice(users)
            
            # 随机选择一个用户作为触发者
            actor = random.choice([u for u in users if u.id != user.id]) if len(users) > 1 else user
            
            # 随机选择通知类型
            notification_type = random.choice(["like", "comment", "follow", "mention", "chase"])
            
            # 随机选择关联对象
            object_id = ""
            if notification_type in ["like", "comment", "mention"]:
                object_id = str(random.choice(posts + comments).id)
            else:
                object_id = random.choice(users).id if notification_type == "follow" else str(random.choice(posts).id)
                
            # 随机选择相关对象ID
            related_id = str(random.choice(comments).id) if notification_type == "comment" and random.random() < 0.5 and comments else None
            
            # 创建通知内容
            content = ""
            if notification_type == "like":
                content = f"{actor.name} 点赞了你的{random.choice(['帖子', '评论'])}"
            elif notification_type == "comment":
                content = f"{actor.name} 评论了你的帖子"
            elif notification_type == "follow":
                content = f"{actor.name} 关注了你"
            elif notification_type == "mention":
                content = f"{actor.name} 在{random.choice(['帖子', '评论'])}中提到了你"
            elif notification_type == "chase":
                content = f"{actor.name} 关注了你的帖子"
            
            # 通知时间
            delivered_at = random_date()
            
            notification = Notification(
                user_id=user.id,
                actor_id=actor.id,
                type=notification_type,
                object_id=object_id,
                related_id=related_id,
                content=content,
                is_read=random.choice([False, False, True]),  # 大多数是未读的
                delivered_at=delivered_at,
                created_at=delivered_at,
                updated_at=delivered_at,
                metadata={
                    "url": f"/post/{random.choice(posts_ids)}" if notification_type in ["like", "comment", "mention", "chase"] else f"/user/{actor.id}",
                    "icon": random.choice(["heart", "comment", "user-plus", "at", "bell"])
                }
            )
            await notification.insert()
            notifications.append(notification)
        except Exception as e:
            print(f"创建通知失败: {str(e)}")
    
    print(f"创建了 {len(notifications)} 个通知")
    return notifications

# 主函数
async def main():
    # 连接数据库
    print(f"连接数据库: {settings.MONGODB_URL}/{settings.DATABASE_NAME}")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    # 初始化Beanie
    await init_beanie(
        database=db,
        document_models=[
            User, Post, Comment, Like, Favorite, 
            Chase, Follow, Push, Notification, Agent
        ]
    )
    
    try:
        
        
        # 从服务获取最新的数据 - 重要的修改：正确处理返回元组
        print("获取所有活跃用户和代理...")
        users_tuple = await UserService.get_users_with_filter(
            UserFilter(status="active"), 
            PaginationParams(page=1, page_size=50)
        )
        await create_agents(users_tuple[0])
        agents_tuple = await AgentService.get_agents_with_filter_unauth(
            AgentFilter(status="active"), 
            PaginationParams(page=1, page_size=50)
        )
        # 提取用户列表（第一个元素）
        users_list = users_tuple[0]
        agents_list = agents_tuple[0]
        
        print(f"获取到 {len(users_list)} 个用户和 {len(agents_list)} 个代理")
        
        # 使用获取到的列表创建其他数据
        posts = await create_posts(agents_list)
        # comments = await create_comments(users_list, posts)
        # likes = await create_likes(users_list, posts, comments)
        # favorites = await create_favorites(users_list, posts)
        # chases = await create_chases(users_list, agents_list)
        # follows = await create_follows(users_list, agents_list)
        # pushes = await create_pushes(users_list, posts)
        # notifications = await create_notifications(users_list, posts, comments)
        
        # 导出生成的ID映射，以便于测试时使用
        # id_mapping = {
        #     "users": [str(user.id) for user in users_list],
        #     "agents": [str(agent.id) for agent in agents_list],
        #     "posts": posts_ids,
        #     "comments": comments_ids,
        #     "likes": [str(like.id) for like in likes if like],
        #     "favorites": [str(favorite.id) for favorite in favorites if favorite],
        #     "chases": [str(chase.id) for chase in chases if chase],
        #     "follows": [str(follow.id) for follow in follows if follow],
        #     "pushes": [str(push.id) for push in pushes if push],
        #     "notifications": [str(notification.id) for notification in notifications if notification]
        # }
        
        # with open("fake_data_ids.json", "w") as f:
        #     json.dump(id_mapping, f, indent=2)
        
        print("假数据生成完成！ID映射已保存到fake_data_ids.json")
    except Exception as e:
        print(f"生成假数据时发生错误: {str(e)}")
        traceback.print_exc()

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())