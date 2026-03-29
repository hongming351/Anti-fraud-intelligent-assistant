from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    
    # 插入初始诈骗模式数据
    db = SessionLocal()
    try:
        from .models import FraudPattern
        from . import schemas
        
        # 检查是否已有数据
        existing_patterns = db.query(FraudPattern).count()
        if existing_patterns == 0:
            # 插入初始诈骗模式
            initial_patterns = [
                schemas.FraudPatternCreate(
                    pattern_type="impersonation",
                    keywords="公安局,检察院,法院,安全账户,涉嫌洗钱,冻结账户,保证金",
                    description="冒充公检法诈骗",
                    risk_weight=1.5
                ),
                schemas.FraudPatternCreate(
                    pattern_type="investment",
                    keywords="高回报,稳赚不赔,内幕消息,数字货币,区块链,投资理财",
                    description="投资理财诈骗",
                    risk_weight=1.3
                ),
                schemas.FraudPatternCreate(
                    pattern_type="phishing",
                    keywords="验证码,点击链接,扫码,登录,密码,账号异常",
                    description="钓鱼诈骗",
                    risk_weight=1.2
                ),
                schemas.FraudPatternCreate(
                    pattern_type="shopping",
                    keywords="客服,退款,退货,快递,包裹,中奖,免费",
                    description="购物退款诈骗",
                    risk_weight=1.1
                ),
                schemas.FraudPatternCreate(
                    pattern_type="romance",
                    keywords="交友,恋爱,见面,转账,困难,急需用钱",
                    description="杀猪盘诈骗",
                    risk_weight=1.4
                )
            ]
            
            for pattern in initial_patterns:
                db_pattern = FraudPattern(
                    pattern_type=pattern.pattern_type,
                    keywords=pattern.keywords,
                    description=pattern.description,
                    risk_weight=pattern.risk_weight
                )
                db.add(db_pattern)
            
            db.commit()
            print("初始诈骗模式数据已插入")
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        db.rollback()
    finally:
        db.close()
