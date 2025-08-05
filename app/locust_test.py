import json
import random
import string
from typing import Dict, Any, Optional, List
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import faker
import uuid
import time
from datetime import datetime, timedelta

# 配置虚假数据生成器
fake = faker.Faker('en_US')

class UndefinedBackendUser(HttpUser):
    """
    模拟用户行为的Locust用户类
    适配Auth0集成的认证系统
    """
    
    wait_time = between(0.05, 0.1) 
    weight = 90  # 普通用户权重
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.email: Optional[str] = None
        self.password: str = "Test123456!"  # Auth0要求密码有一定复杂度
        self.auth_headers: Dict[str, str] = {}
        self.followed_agents: List[str] = []
        self.visited_posts: List[str] = []
        self.created_comments: List[Dict[str, str]] = []  # [{"id": "xxx", "user_id": "yyy", "created_at": "zzz"}]

        
    def on_start(self):
        """用户开始时执行登录"""
        # 由于Auth0注册需要真实的邮箱验证，我们主要使用预设的测试用户
        login_delay = random.uniform(0, 1)  # 0-1秒随机延迟
        print(f"🕐 用户 {self.email} 将在 {login_delay:.1f} 秒后登录")
        time.sleep(login_delay)
        self.login_with_test_user()
    
    def on_stop(self):
        """用户停止时清理创建的数据"""
        if not self.access_token or not self.created_comments:
            return
            
        print(f"🧹 用户停止，清理 {len(self.created_comments)} 个创建的评论...")
        
        # 清理所有创建的评论
        for comment_id in self.created_comments.copy():  # 使用copy避免迭代时修改列表
            try:
                with self.client.delete(
                    f"/api/v1/comments/delete/{comment_id}",
                    headers=self.auth_headers,
                    name="最终清理评论"
                ) as response:
                    if response.status_code == 200:
                        print(f"✅ 最终清理评论成功: {comment_id}")
                    else:
                        print(f"⚠️ 最终清理评论失败: {comment_id}")
            except Exception as e:
                print(f"⚠️ 清理评论异常: {comment_id}, {str(e)}")
        
        self.created_comments.clear()
        print("🧹 评论清理完成")
    
    def login_with_test_user(self):
        """使用测试用户登录"""
        # 使用预设的测试用户账号
        test_users = [
            {"email": "test1@example.com", "password": "Test123456!"},
            {"email": "test2@example.com", "password": "Test123456!"},
            {"email": "test3@example.com", "password": "Test123456!"},
            {"email": "test4@example.com", "password": "Test123456!"},
            {"email": "test5@example.com", "password": "Test123456!"},
        ]
        
        user_creds = random.choice(test_users)
        self.email = user_creds["email"]
        self.password = user_creds["password"]
        self.login()
    
    def login(self):
        """用户登录 - 适配Auth0"""
        login_data = {
            "email": self.email,
            "password": self.password
        }
        with self.client.post(
            "/api/v1/users/login_by_email",
            json=login_data,
            catch_response=True,
            name="用户登录"
        ) as response:
            print(f"login.response: \n{response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("message") == "success" and data.get("data"):
                        self.access_token = data["data"].get("access_token")
                        user_info = data["data"].get("user")
                        if user_info:
                            self.user_id = user_info.get("id")
                        
                        self.auth_headers = {
                            "Authorization": f"Bearer {self.access_token}"
                        }
                        response.success()
                        return
                except Exception as e:
                    response.failure(f"解析登录响应失败: {str(e)}")
                    raise StopUser()
            response.failure(f"登录失败: {response.text}")
            # 登录失败则停止用户
            raise StopUser()
    
    @task(25)
    def browse_posts(self):
        """浏览帖子列表"""
        if not self.access_token:
            return
            
        params = {
            "page": random.randint(1, 5),
            "page_size": random.randint(10, 20),
            "sort_by": random.choice(["created_at", "updated_at"]),
            "sort_desc": random.choice([True, False])
        }
        
        with self.client.get(
            "/api/v1/posts/get_posts_with_filter",
            params=params,
            headers=self.auth_headers,
            name="浏览帖子列表",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"🔍 帖子响应数据: {data}")  # 添加调试信息
                    
                    # 修复响应检查逻辑
                    if data.get("message") == "success" and data.get("data", {}).get("items"):
                        posts = data["data"]["items"]
                        print(f"📝 获取到 {len(posts)} 个帖子")
                        
                        # 记录访问过的帖子
                        for post in posts[:3]:
                            if post.get("post"):
                                post = post["post"]
                                if post["id"] not in self.visited_posts:  # 避免重复
                                    self.visited_posts.append(post["id"])
                                    print(f"➕ 添加帖子ID: {post['id']} | {post['title']}")
                        
                        print(f"📋 当前visited_posts数量: {len(self.visited_posts)}")
                    else:
                        print(f"⚠️ 帖子响应格式异常: {data}")
                except Exception as e:
                    print(f"❌ 解析帖子响应失败: {str(e)}")
                response.success()
            else:
                response.failure(f"浏览帖子失败: {response.text}")
        
    @task(20)
    def view_post_detail(self):
        """查看帖子详情"""
        if not self.visited_posts or not self.access_token:
            return
            
        post_id = random.choice(self.visited_posts)
        with self.client.get(
            f"/api/v1/posts/get_post_by_id/{post_id}",
            headers=self.auth_headers,
            name="查看帖子详情",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("message") == "success" and data.get("data"):
                        post_data = data["data"]
                        print(f"查看帖子: {post_data.get('title', '无标题')}")
                    response.success()
                except:
                    pass
            else:
                response.failure(f"查看帖子详情失败: {response.text}")
    
    @task(20)
    def browse_agents(self):
        """浏览agent列表"""
        if not self.access_token:
            return
            
        params = {
            "page": random.randint(1, 3),
            "page_size": random.randint(10, 15),
            "sort_by": random.choice(["created_at", "follower_count"]),
            "sort_desc": True
        }
        
        # 随机添加标签过滤
        if random.random() < 0.4:
            tags = random.sample(["AI助手", "客服", "教育", "娱乐", "工具"], 
                               random.randint(1, 2))
            for tag in tags:
                params[f"tags"] = tag
        
        with self.client.get(
            "/api/v1/agents/get_agents_with_filter",
            params=params,
            headers=self.auth_headers,
            name="浏览agent列表",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("message") == "success" and data.get("data", {}).get("items"):
                        agents = data["data"]["items"]
                        # 记录可关注的agent
                        for agent in agents[:2]:
                            if agent.get("id") and agent["id"] not in self.followed_agents:
                                self.followed_agents.append(agent["id"])
                except:
                    pass
                response.success()
            else:
                response.failure(f"浏览agent失败: {response.text}")
    
    @task(15)
    def view_agent_detail(self):
        """查看agent详情"""
        if not self.followed_agents or not self.access_token:
            return
            
        agent_id = random.choice(self.followed_agents)
        with self.client.get(
            f"/api/v1/agents/get_agent_by_id/{agent_id}",
            headers=self.auth_headers,
            name="查看agent详情",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看agent详情失败: {response.text}")
    
    @task(12)
    def like_post_toggle(self):
        """点赞帖子（点赞+取消，保持状态一致）"""
        if not self.visited_posts or not self.access_token:
            return
            
        post_id = random.choice(self.visited_posts)
        
        # 第一次：点赞
        like_data = {
            "target_id": post_id,
            "target_type": "post",
            "is_like": True
        }
        
        with self.client.post(
            "/api/v1/likes/like_click",
            json=like_data,
            headers=self.auth_headers,
            name="点赞帖子",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"✅ 点赞帖子成功: {post_id}")
                
                # 第二次：取消点赞（保持状态一致）
                unlike_data = {
                    "target_id": post_id,
                    "target_type": "post", 
                    "is_like": False
                }
                
                with self.client.post(
                    "/api/v1/likes/like_click",
                    json=unlike_data,
                    headers=self.auth_headers,
                    name="取消点赞帖子",
                    catch_response=True
                ) as unlike_response:
                    if unlike_response.status_code == 200:
                        print(f"✅ 取消点赞成功: {post_id}")
                    else:
                        unlike_response.failure(f"取消点赞失败: {unlike_response.text}")
                        
                response.success()
            else:
                response.failure(f"点赞失败: {response.text}")
    
    @task(10)
    def favorite_post_toggle(self):
        """收藏帖子（收藏+取消，保持状态一致）"""
        if not self.visited_posts or not self.access_token:
            return
            
        post_id = random.choice(self.visited_posts)
        
        # 第一次：收藏
        favorite_data = {
            "target_id": post_id,
            "target_type": "post",
            "is_favorite": True
        }
        
        with self.client.post(
            "/api/v1/favorites/favorite_click",
            json=favorite_data,
            headers=self.auth_headers,
            name="收藏帖子",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"⭐ 收藏帖子成功: {post_id}")
                
                # 第二次：取消收藏（保持状态一致）
                unfavorite_data = {
                    "target_id": post_id,
                    "target_type": "post",
                    "is_favorite": False
                }
                
                with self.client.post(
                    "/api/v1/favorites/favorite_click",
                    json=unfavorite_data,
                    headers=self.auth_headers,
                    name="取消收藏帖子",
                    catch_response=True
                ) as unfavorite_response:
                    if unfavorite_response.status_code == 200:
                        print(f"✅ 取消收藏成功: {post_id}")
                    else:
                        unfavorite_response.failure(f"取消收藏失败: {unfavorite_response.text}")
                        
                response.success()
            else:
                response.failure(f"收藏失败: {response.text}")
    
    @task(8)
    def comment_on_post(self):
        """评论帖子 - 改进版，记录更多评论信息"""
        if not self.visited_posts or not self.access_token:
            return
        
        # 限制每个用户最多创建10个评论，避免数据过多
        if len(self.created_comments) >= 10:
            print(f"⚠️ 已创建评论数量达到上限({len(self.created_comments)})，跳过创建")
            return
            
        post_id = random.choice(self.visited_posts)
        
        comment_data = {
            "target_id": post_id,
            "target_type": "post",
            "content": fake.text(max_nb_chars=200),
            "parent_id": ""  # 顶级评论
        }
        
        with self.client.post(
            "/api/v1/comments/create",
            json=comment_data,
            headers=self.auth_headers,
            name="评论帖子",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("message") == "success" and data.get("data"):
                        comment_info = {
                            "id": data["data"].get("id"),
                            "user_id": self.user_id,
                            "created_at": time.time(),
                            "post_id": post_id
                        }
                        if comment_info["id"]:
                            self.created_comments.append(comment_info)
                            print(f"💬 评论成功: {comment_info['id']} (总计: {len(self.created_comments)})")
                except:
                    pass
                response.success()
            else:
                response.failure(f"评论失败: {response.text}")
    
    @task(6)
    def like_comment_toggle(self):
        """点赞评论（点赞+取消，保持状态一致）"""
        if not self.created_comments or not self.access_token:
            return
            
        comment_id = random.choice(self.created_comments)["id"]
        
        # 第一次：点赞评论
        like_data = {
            "target_id": comment_id,
            "target_type": "comment",
            "is_like": True
        }
        
        with self.client.post(
            "/api/v1/likes/like_click",
            json=like_data,
            headers=self.auth_headers,
            name="点赞评论",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"👍 点赞评论成功: {comment_id}")
                
                # 第二次：取消点赞评论
                unlike_data = {
                    "target_id": comment_id,
                    "target_type": "comment",
                    "is_like": False
                }
                
                with self.client.post(
                    "/api/v1/likes/like_click",
                    json=unlike_data,
                    headers=self.auth_headers,
                    name="取消点赞评论",
                    catch_response=True
                ) as unlike_response:
                    if unlike_response.status_code == 200:
                        print(f"✅ 取消点赞评论成功: {comment_id}")
                    else:
                        unlike_response.failure(f"取消点赞评论失败: {unlike_response.text}")
                        
                response.success()
            else:
                response.failure(f"点赞评论失败: {response.text}")
    
    @task(6)
    def follow_agent_toggle(self):
        """关注agent（关注+取消，保持状态一致）"""
        if not self.followed_agents or not self.access_token:
            return
            
        agent_id = random.choice(self.followed_agents)
        
        # 第一次：关注
        follow_data = {
            "agent_id": agent_id,
            "is_follow": True
        }
        
        with self.client.post(
            "/api/v1/follows/follow_click",
            json=follow_data,
            headers=self.auth_headers,
            name="关注agent",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"👥 关注agent成功: {agent_id}")
                
                # 第二次：取消关注（保持状态一致）
                unfollow_data = {
                    "agent_id": agent_id,
                    "is_follow": False
                }
                
                with self.client.post(
                    "/api/v1/follows/follow_click",
                    json=unfollow_data,
                    headers=self.auth_headers,
                    name="取消关注agent",
                    catch_response=True
                ) as unfollow_response:
                    if unfollow_response.status_code == 200:
                        print(f"✅ 取消关注成功: {agent_id}")
                    else:
                        unfollow_response.failure(f"取消关注失败: {unfollow_response.text}")
                        
                response.success()
            else:
                response.failure(f"关注失败: {response.text}")
    
    @task(4)
    def view_my_follows(self):
        """查看我的关注列表"""
        if not self.access_token:
            return
            
        params = {
            "page": 1,
            "page_size": 10
        }
        
        with self.client.get(
            "/api/v1/follows/get_follows_with_filter",
            params=params,
            headers=self.auth_headers,
            name="查看关注列表",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看关注列表失败: {response.text}")
    
    @task(15)
    def view_post_comments(self):
        """查看帖子评论"""
        if not self.visited_posts or not self.access_token:
            return
            
        post_id = random.choice(self.visited_posts)
        params = {
            "target_id": post_id,
            "limit": 10
        }
        
        with self.client.get(
            "/api/v1/comments/target_id",
            params=params,
            headers=self.auth_headers,
            name="查看帖子评论",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("message") == "success" and data.get("data"):
                        comments = data["data"].get("items", [])
                        print(f"💬 帖子 {post_id} 有 {len(comments)} 条评论")
                    response.success()
                except:
                    pass
            else:
                response.failure(f"查看帖子评论失败: {response.text}")

    @task(3)
    def get_current_user_info(self):
        """获取当前用户信息"""
        if not self.access_token:
            return
            
        with self.client.get(
            "/api/v1/users/get_current_user",
            headers=self.auth_headers,
            name="获取用户信息",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"获取用户信息失败: {response.text}")

    @task(2)
    def cleanup_created_comments(self):
        """定期清理创建的评论"""
        if not self.created_comments or not self.access_token:
            return
        
        # 一次最多清理3个评论
        comments_to_delete = self.created_comments[:3]
        
        for comment_info in comments_to_delete:
            comment_id = comment_info["id"] if isinstance(comment_info, dict) else comment_info
            
            with self.client.delete(
                f"/api/v1/comments/delete/{comment_id}",
                headers=self.auth_headers,
                name="删除创建的评论",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    print(f"🗑️ 删除评论成功: {comment_id}")
                    self.created_comments.remove(comment_info)
                    response.success()
                else:
                    print(f"❌ 删除评论失败: {comment_id}, 状态码: {response.status_code}")
                    response.failure(f"删除评论失败: {response.text}")
                    # 从列表中移除，避免重复尝试
                    if comment_info in self.created_comments:
                        self.created_comments.remove(comment_info)


# 事件监听器
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("🚀 开始压力测试...")
    print(f"目标: 模拟 {environment.parsed_options.num_users if environment.parsed_options else '未指定'} 并发用户")
    print("主要测试场景:")
    print("- 用户登录 (集成Auth0)")
    print("- 浏览帖子和agent")
    print("- 点赞、评论、关注等互动")
    print("- 智能评论清理机制")
    print("")
    print("⚠️  注意：由于集成了Auth0，请确保：")
    print("1. 已在Auth0中创建测试用户")
    print("2. Auth0服务正常运行")
    print("3. 网络连接稳定")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("✅ 压力测试完成!")
    print("📊 建议查看以下指标:")
    print("- Auth0 API调用次数和响应时间")
    print("- 数据库连接池使用情况") 
    print("- Redis缓存命中率")
    print("- 创建评论的清理情况")