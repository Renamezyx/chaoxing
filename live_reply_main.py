import random
import time

from api.answer import Tiku
from api.base import Account, Chaoxing
from main import RollBackManager, init_config
from api.exceptions import LoginError, FormatError, JSONDecodeError, MaxRollBackError
from api.logger import logger

if __name__ == '__main__':
    # 避免异常的无限回滚
    RB = RollBackManager()
    # 初始化登录信息
    common_config, tiku_config = init_config()
    username = common_config.get("username", "")
    password = common_config.get("password", "")
    course_list = common_config.get("course_list", None)
    speed = common_config.get("speed", 1)
    query_delay = tiku_config.get("delay", 0)
    # 规范化播放速度的输入值
    speed = min(2.0, max(1.0, speed))
    if (not username) or (not password):
        username = input("请输入你的手机号, 按回车确认\n手机号:")
        password = input("请输入你的密码, 按回车确认\n密码:")
    account = Account(username, password)
    # 设置题库
    tiku = Tiku()
    tiku.config_set(tiku_config)  # 载入配置
    tiku = tiku.get_tiku_from_config()  # 载入题库
    tiku.init_tiku()  # 初始化题库

    # 实例化超星API
    chaoxing = Chaoxing(account=account, tiku=tiku, query_delay=query_delay)
    # 检查当前登录状态, 并检查账号密码
    _login_state = chaoxing.login()
    if not _login_state["status"]:
        raise LoginError(_login_state["msg"])
    # 获取所有的课程列表
    all_course = chaoxing.get_course_list()
    course_task = []
    # 手动输入要学习的课程ID列表
    if not course_list:
        print("*" * 10 + "课程列表" + "*" * 10)
        for course in all_course:
            print(f"ID: {course['courseId']} 课程名: {course['title']}")
        print("*" * 28)
        try:
            course_list = input(
                "请输入想要学习的课程列表,以逗号分隔,例: 2151141,189191,198198\n"
            ).split(",")
        except Exception as e:
            raise FormatError("输入格式错误") from e
    # 筛选需要学习的课程
    for course in all_course:
        if course["courseId"] in course_list:
            course_task.append(course)
    if not course_task:
        course_task = all_course
    # 开始遍历要学习的课程列表
    logger.info(f"课程列表过滤完毕, 当前课程任务数量: {len(course_task)}")
    for course in course_task:
        logger.info(f"开始学习课程: {course['title']}")
        # 获取当前课程的所有章节
        point_list = chaoxing.get_course_point(
            course["courseId"], course["clazzId"], course["cpi"]
        )
        __point_index = 0
        point_list['points'] = [
            point for point in point_list['points']
            if any(keyword in point['title'] for keyword in ["直播回看", "直播入口", "课堂教学"])
        ]
        while __point_index < len(point_list["points"]):
            point = point_list["points"][__point_index]
            logger.info(f'当前章节: {point["title"]}')
            logger.debug(f"当前章节 __point_index: {__point_index}")  # 触发参数: -v
            sleep_duration = random.uniform(1, 3)
            logger.debug(f"本次随机等待时间: {sleep_duration}")
            chaoxing.study_live_replay(_chapterId=point["id"], _courseid=course["courseId"], _clazzid=course["clazzId"],
                                       _cpi=course["cpi"], enc=point_list["enc"])
            logger.info(f'完成当前章节: {point["title"]}')
            __point_index += 1
