# -*- coding: utf-8 -*-
"""
独角兽语音数据爬取器
从碧蓝航线wiki提取独角兽的所有语音文件
用于So-VITS-SVC模型训练
"""

import re
import urllib.request
import os
from pathlib import Path
import time
import requests
from bs4 import BeautifulSoup

class UnicornVoiceScraper:
    def __init__(self):
        self.base_dir = Path("./so-vits-svc-4.1-Stable")
        self.dataset_dir = self.base_dir / "dataset_raw" / "unicorn"
        self.voice_data = []
        
        # 创建目录
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_voice_data_from_html(self, html_content):
        """从HTML内容中提取语音数据"""
        print("解析独角兽语音数据...")
        
        # 基于实际HTML数据提取的完整语音数据 - 包含基础和皮肤语音
        voice_data = [
            # === 基础语音 ===
            {"text": "碧蓝航线五周年快乐", "url": "https://patchwiki.biligame.com/images/blhx/4/4a/0g232eytuxjbm1nsvrd1v2u1yudcmkx.mp3", "type": "anniversary", "scene": "五周年登录", "skin": "基础"},
            {"text": "皇家海军支援空母独角兽原本是为了支援光辉姐姐而诞生的后来也和许多其他姐姐们一起行动过大家对我都很好呢独角兽在很多地方都努力过能派上用场就好了呢嘻嘻我会更加努力的哥哥", "url": "https://patchwiki.biligame.com/images/blhx/2/2e/joqqxarlt9mcbycx1yntm8kbszyuv8k.mp3", "type": "profile", "scene": "自我介绍", "skin": "基础"},
            {"text": "啊我是皇家海军独角兽指挥官能叫你哥哥吗", "url": "https://patchwiki.biligame.com/images/blhx/1/11/nnzmn34qi8cwz0tp8nqvtn71p5ssdav.mp3", "type": "unlock", "scene": "获取台词", "skin": "基础"},
            {"text": "欢迎回来哥哥今天也要出击吗", "url": "https://patchwiki.biligame.com/images/blhx/4/44/7m9o9sk2qkuikwkrjpdlsg16rxk2k5y.mp3", "type": "login", "scene": "登录台词", "skin": "基础"},
            {"text": "哥哥想要更多了解独角兽吗", "url": "https://patchwiki.biligame.com/images/blhx/2/2c/adiwo5k4k4royu0zjurbdvpyci07egx.mp3", "type": "detail", "scene": "查看详情", "skin": "基础"},
            {"text": "毁灭模式什么的是不存在的喔", "url": "https://patchwiki.biligame.com/images/blhx/d/d6/kfkfavoxqnqpymejkwcv3w20a2reobg.mp3", "type": "main_1", "scene": "主界面1", "skin": "基础"},
            {"text": "优酱的角是不会变形的喔", "url": "https://patchwiki.biligame.com/images/blhx/e/e5/04pgw7qj1jykpl5h95b5i6evi4f2u1f.mp3", "type": "main_2", "scene": "主界面2", "skin": "基础"},
            {"text": "NーTーD对不起独角兽不知道哥哥在说什么", "url": "https://patchwiki.biligame.com/images/blhx/9/99/trhcwcqr0sbpesdvef5dcn3n9z90rvw.mp3", "type": "main_3", "scene": "主界面3", "skin": "基础"},
            {"text": "独角兽有一天也能变成光辉姐姐那样成熟的大人吗", "url": "https://patchwiki.biligame.com/images/blhx/9/9b/3v3dgsnvp7q4avg8w0i0y1gu71h6ow7.mp3", "type": "main_4", "scene": "主界面4", "skin": "基础"},
            {"text": "嘻嘻好痒的啦哥哥", "url": "https://patchwiki.biligame.com/images/blhx/3/31/3eylzbju2q38huzd5t5fcvnubkblavw.mp3", "type": "touch", "scene": "触摸台词", "skin": "基础"},
            {"text": "哥哥的话可以喔", "url": "https://patchwiki.biligame.com/images/blhx/9/98/pl3kieuezrh96qr5bj2629565c2z7tu.mp3", "type": "special_touch", "scene": "特殊触摸", "skin": "基础"},
            {"text": "哥哥独角兽是乖孩子吧", "url": "https://patchwiki.biligame.com/images/blhx/4/4e/blhg6t7r35yphex1lzi8hhlpkjkggr6.mp3", "type": "head_touch", "scene": "摸头台词", "skin": "基础"},
            {"text": "任务不要忘记", "url": "https://patchwiki.biligame.com/images/blhx/f/fb/rxfy0r8596fatw8m7bwn9tttkhg2bn9.mp3", "type": "mission", "scene": "任务提醒", "skin": "基础"},
            {"text": "奖励不能错过", "url": "https://patchwiki.biligame.com/images/blhx/9/96/fxq1h8e9fmnusj378tmlrs00iup1nzk.mp3", "type": "mission_complete", "scene": "任务完成", "skin": "基础"},
            {"text": "邮件要去看看吗", "url": "https://patchwiki.biligame.com/images/blhx/e/eb/1y0cgfme1uixaf90plcg6il8zl5jslz.mp3", "type": "mail", "scene": "邮件提醒", "skin": "基础"},
            {"text": "舰队平安回港哥哥辛苦了膝枕也可以的喔", "url": "https://patchwiki.biligame.com/images/blhx/0/01/fgyhdihomkju7llljv3zws0chetiuhy.mp3", "type": "home", "scene": "回港台词", "skin": "基础"},
            {"text": "哥哥差劲", "url": "https://patchwiki.biligame.com/images/blhx/c/c4/0x6fzdnxv2yv1z2odrt7c6tq7rgnsf8.mp3", "type": "feeling_disappointed", "scene": "好感度失望", "skin": "基础"},
            {"text": "这孩子叫做优酱独角兽的优酱是我的挚友喔嘻嘻", "url": "https://patchwiki.biligame.com/images/blhx/e/eb/q2g1bv1kerlifk5n35ib9uikx52xeza.mp3", "type": "feeling_stranger", "scene": "好感度陌生", "skin": "基础"},
            {"text": "遇到危险的时候优酱会保护我的有哥哥在就不会有危险嘻嘻哥哥好像独角兽的骑士呢", "url": "https://patchwiki.biligame.com/images/blhx/0/09/3ksl6ad50acw8bogc23qps0u8z9dew5.mp3", "type": "feeling_friendly", "scene": "好感度友好", "skin": "基础"},
            {"text": "独角兽一直很努力支援姐姐们也好出击任务也好运输任务也好独角兽是乖孩子吧有派上用场吧哥哥", "url": "https://patchwiki.biligame.com/images/blhx/8/87/qtfcj9zzojymh067igq6vywv2047q2g.mp3", "type": "feeling_like", "scene": "好感度喜欢", "skin": "基础"},
            {"text": "在哥哥面前任性也可以吗撒娇也可以吗独角兽其实不是那么听话的孩子这样也可以吗", "url": "https://patchwiki.biligame.com/images/blhx/6/64/bravy1rjjis4h0aw4zqgrhh13vabnlh.mp3", "type": "feeling_love", "scene": "好感度爱", "skin": "基础"},
            {"text": "这么重要的独角兽真的可以吗独角兽会加油的因为最喜欢哥哥了", "url": "https://patchwiki.biligame.com/images/blhx/6/62/c586gkv5hnds4fna10dmitm7f0xe19s.mp3", "type": "propose", "scene": "誓约台词", "skin": "基础"},
            {"text": "委托组的姐姐们回来了一起去迎接她们吗哥哥", "url": "https://patchwiki.biligame.com/images/blhx/9/97/jz9c9ywwcwmormfud2m2ontp9z3cb6q.mp3", "type": "expedition", "scene": "委托完成", "skin": "基础"},
            {"text": "独角兽成长了吗哥哥", "url": "https://patchwiki.biligame.com/images/blhx/9/9b/53hn6ppk13uszep2j38os6ujaqpza0v.mp3", "type": "upgrade", "scene": "强化成功", "skin": "基础"},
            {"text": "后方支援就交给我吧独角兽会加油的", "url": "https://patchwiki.biligame.com/images/blhx/9/96/4sjjmgs7t9wdqkjbj7zv7d4xbf32rtb.mp3", "type": "battle", "scene": "旗舰开战", "skin": "基础"},
            {"text": "独角兽这次有帮上哥哥的忙吗", "url": "https://patchwiki.biligame.com/images/blhx/1/1b/i9rcfefq15ez5uuxxgg79hjwvtu1eem.mp3", "type": "victory", "scene": "胜利台词", "skin": "基础"},
            {"text": "外面好可怕独角兽可以回家吗哥哥", "url": "https://patchwiki.biligame.com/images/blhx/f/fc/n6ys9f2g46tvbevgglouhtyxabec0wu.mp3", "type": "lose", "scene": "失败台词", "skin": "基础"},
            {"text": "独角兽会努力的", "url": "https://patchwiki.biligame.com/images/blhx/0/0e/ssfwpsqkkmwyno493iwvz4klwk30sv1.mp3", "type": "skill", "scene": "技能台词", "skin": "基础"},
            {"text": "哥哥好痛", "url": "https://patchwiki.biligame.com/images/blhx/b/bf/phdvlvtvgy0qlsjcl0x5kv0onud9z7m.mp3", "type": "hp_warning", "scene": "血量告急", "skin": "基础"},
            {"text": "光辉姐姐的援护就交给我吧", "url": "https://patchwiki.biligame.com/images/blhx/7/7a/6hlpq7w7at55zo6aapllbw0ag81gkf2.mp3", "type": "couple_1", "scene": "彩蛋台词1", "skin": "基础"},
            {"text": "不要欺负我的朋友", "url": "https://patchwiki.biligame.com/images/blhx/b/b2/7kfgry5f8fh9q7bedqe11gju7n9r2nw.mp3", "type": "couple_2", "scene": "彩蛋台词2", "skin": "基础"},
            {"text": "独角兽喜欢唱歌不过在大家面前还是", "url": "https://patchwiki.biligame.com/images/blhx/c/c3/j790dt4nofho746mrfbk8vdi52abgzf.mp3", "type": "couple_3", "scene": "彩蛋台词3", "skin": "基础"},
            
            # === 皮肤语音 - 小小的星之歌姬 ===
            {"text": "独角兽变成歌姬了诶嘿嘿独角兽的歌能传达到哥哥的心里就好了", "url": "https://patchwiki.biligame.com/images/blhx/c/c9/7yvc4icn6og0qy0b9oxiibrisy50hi9.mp3", "type": "singer_desc", "scene": "歌姬获取", "skin": "小小的星之歌姬"},
            {"text": "独角兽穿上这么华丽的衣服真的合适吗哥哥", "url": "https://patchwiki.biligame.com/images/blhx/5/56/72klwf66t2v3p565uhrbmlvwprl6vs8.mp3", "type": "singer_main1", "scene": "歌姬主界面1", "skin": "小小的星之歌姬"},
            {"text": "优酱也成长了呢嘻嘻", "url": "https://patchwiki.biligame.com/images/blhx/e/e5/q1tu225wn54adzhnxjp3cfv09s7wz3n.mp3", "type": "singer_main2", "scene": "歌姬主界面2", "skin": "小小的星之歌姬"},
            {"text": "听我唱歌吧嘻嘻独角兽是不是有点歌姬的样子了呢", "url": "https://patchwiki.biligame.com/images/blhx/6/62/3pyj185e6is68ntm4rwlpta5npn2wsd.mp3", "type": "singer_main3", "scene": "歌姬主界面3", "skin": "小小的星之歌姬"},
            {"text": "光辉姐姐独角兽有没有变得成熟一点了呢", "url": "https://patchwiki.biligame.com/images/blhx/2/2e/g2wtmnrp2h12mj108fxrfspipo7of0i.mp3", "type": "singer_main4", "scene": "歌姬主界面4", "skin": "小小的星之歌姬"},
            {"text": "嘻嘻想听独角兽的歌吗哥哥", "url": "https://patchwiki.biligame.com/images/blhx/e/e6/jkxi93f6bf72gky2by5ykahr0y3tx7y.mp3", "type": "singer_touch", "scene": "歌姬触摸", "skin": "小小的星之歌姬"},
            
            # === 皮肤语音 - 春之礼 ===
            {"text": "这个送给哥哥希望哥哥会喜欢欸穿上这件衣服就是最好的礼物哥哥", "url": "https://patchwiki.biligame.com/images/blhx/e/e3/gn321hgnivvdyg5t01sucfsogipaii6.mp3", "type": "spring_desc", "scene": "春之礼获取", "skin": "春之礼"},
            {"text": "哥哥请不要一直盯着独角兽看呜", "url": "https://patchwiki.biligame.com/images/blhx/2/2d/tdov12sn2icvklr47hivrd37a1bsjw5.mp3", "type": "spring_detail", "scene": "春之礼详情", "skin": "春之礼"},
            {"text": "这个叫做春联字是东煌的姐姐们教独角兽写的呢欸嘿嘿", "url": "https://patchwiki.biligame.com/images/blhx/5/5d/23hn2o5szw8fm6orha2ojn5a0rhqkks.mp3", "type": "spring_main1", "scene": "春之礼主界面1", "skin": "春之礼"},
            {"text": "爆竹好像是东煌的特产呢啊这个是装饰不会爆炸的", "url": "https://patchwiki.biligame.com/images/blhx/9/94/4kc51vnctcf28kqw4s4kvqr24awbqae.mp3", "type": "spring_main2", "scene": "春之礼主界面2", "skin": "春之礼"},
            {"text": "哥哥独角兽有没有稍微成熟一点呢", "url": "https://patchwiki.biligame.com/images/blhx/e/e5/2y467kuibpb2bhur1nvfrt1n1s9l8u2.mp3", "type": "spring_main3", "scene": "春之礼主界面3", "skin": "春之礼"},
            
            # === 皮肤语音 - 憧憬的约会日 ===
            {"text": "啊哥哥你来了嘻嘻独角兽也刚到没多久哦那我们出发吧游乐园有点期待", "url": "https://patchwiki.biligame.com/images/blhx/0/0b/djtqdofy1he4lf7htjpofh2nbq7jvd6.mp3", "type": "date_desc", "scene": "约会日获取", "skin": "憧憬的约会日"},
            {"text": "哥哥独角兽有好多想和哥哥一起玩的项目", "url": "https://patchwiki.biligame.com/images/blhx/5/51/qvwub5jkt0g8rmwuobie7syirf7w6m3.mp3", "type": "date_login", "scene": "约会日登录", "skin": "憧憬的约会日"},
            {"text": "哥哥坐过山车的时候能握着你的手吗", "url": "https://patchwiki.biligame.com/images/blhx/3/36/kvdq7w0yw0vies2wz2n0yi1wjijgkhn.mp3", "type": "date_main1", "scene": "约会日主界面1", "skin": "憧憬的约会日"},
            {"text": "摩天轮推荐情侣共乘诶啊哥哥没没什么", "url": "https://patchwiki.biligame.com/images/blhx/1/17/aj0kovuiarvchbrpw6sais9di67zdiw.mp3", "type": "date_main2", "scene": "约会日主界面2", "skin": "憧憬的约会日"},
            {"text": "旋转木马好漂亮诶可以和哥哥一起坐吗", "url": "https://patchwiki.biligame.com/images/blhx/1/14/0ann7ihmvip144rcp5ks0xiatjpevry.mp3", "type": "date_main3", "scene": "约会日主界面3", "skin": "憧憬的约会日"},
            {"text": "像这样在游乐园和哥哥手牵手总觉得就像恋人一样呢嘻嘻", "url": "https://patchwiki.biligame.com/images/blhx/b/b6/qjvz5cvmtib8jsdnzwzlihflq6osz0e.mp3", "type": "date_touch", "scene": "约会日触摸", "skin": "憧憬的约会日"},
            {"text": "哥哥这里人有点多", "url": "https://patchwiki.biligame.com/images/blhx/6/63/7o7sov2tv9mu3ufyr3bd2nqxai8ljac.mp3", "type": "date_special_touch", "scene": "约会日特殊触摸", "skin": "憧憬的约会日"},
            {"text": "本来约会之前想了很多话想对哥哥说但现在觉得不用说也可以了因为独角兽已经知道了哥哥的心意哥哥也能感受的吧和哥哥一样的独角兽的心意", "url": "https://patchwiki.biligame.com/images/blhx/5/5e/08o5qezrvdf0bf344j00jm299ig2zcl.mp3", "type": "date_love", "scene": "约会日爱意", "skin": "憧憬的约会日"},
            
            # === 誓约皮肤语音选取 ===
            {"text": "这是为了重要的仪式而换上的重要的服装嗯独角兽和优酱都准备好了哥哥独角兽这样可以了吗", "url": "https://patchwiki.biligame.com/images/blhx/e/ec/6dc0oq858sltlntlowwhmw6ocgczjpk.mp3", "type": "wedding_unlock", "scene": "誓约获取", "skin": "梦想的纯白誓约"},
            {"text": "哥哥嘻嘻独角兽一直在这里在等着哥哥回来哦", "url": "https://patchwiki.biligame.com/images/blhx/b/b0/pwehscz10c4t6i7hjd4thuuxevcmmgy.mp3", "type": "wedding_login", "scene": "誓约登录", "skin": "梦想的纯白誓约"},
            {"text": "还想和哥哥多牵一会手可以吗", "url": "https://patchwiki.biligame.com/images/blhx/f/f1/rdr5v5oa0kcyuhfarvy8f7hx106vum2.mp3", "type": "wedding_touch", "scene": "誓约触摸", "skin": "梦想的纯白誓约"},
            {"text": "即便独角兽不会成为光辉姐姐那样成熟的大人哥哥也会一直在独角兽身边吧", "url": "https://patchwiki.biligame.com/images/blhx/1/17/ksxpvpynnkycybbclxvutpxgo0u70on.mp3", "type": "wedding_main4", "scene": "誓约深情", "skin": "梦想的纯白誓约"},
            
            # === 其他精选皮肤语音 ===
            {"text": "独角兽变成偶像了虽然不知道能不能做好但是独角兽会加油的", "url": "https://patchwiki.biligame.com/images/blhx/8/8e/qoa3kw1l7lzm59zvp5wnil5oubohbg9.mp3", "type": "idol_desc", "scene": "天使偶像", "skin": "天使的My Night"},
            {"text": "只要还有哥哥这个听众独角兽就会一直一直努力唱下去", "url": "https://patchwiki.biligame.com/images/blhx/8/8b/d39mdd2rultc14aq4wh5ddvkxky9a48.mp3", "type": "idol_touch", "scene": "偶像决心", "skin": "天使的My Night"},
            {"text": "啊哥哥独角兽在看书哦嗯一边吃冰棒哥哥也要来一口吗", "url": "https://patchwiki.biligame.com/images/blhx/2/22/1212z00ahdq78yioyzrb4gh6jo93yx0.mp3", "type": "summer_desc", "scene": "清凉时光", "skin": "清凉阅读时光"},
            {"text": "嗯冰棒好冰不过还是很好吃", "url": "https://patchwiki.biligame.com/images/blhx/5/5b/isykuh0ae2fqva3on94pt6a886jdfys.mp3", "type": "summer_main1", "scene": "夏日冰棒", "skin": "清凉阅读时光"},
            {"text": "独角兽现在是负责护理的护士哦那个哥哥能请你当一下独角兽的病人吗", "url": "https://patchwiki.biligame.com/images/blhx/2/2e/g2jyaqclmpgmu9sv2706fja77smmnum.mp3", "type": "nurse_desc", "scene": "护士装扮", "skin": "天使的护理时间"},
            {"text": "今天的独角兽是哥哥的专属护士呢诶嘿嘿", "url": "https://patchwiki.biligame.com/images/blhx/3/3e/2n5hkpzqrzyifnc57ljxa67je3plbpt.mp3", "type": "nurse_touch", "scene": "专属护士", "skin": "天使的护理时间"},
            {"text": "呼哈嗯哥哥加加油哥哥都那么努力了独角兽也要努力给哥哥加油", "url": "https://patchwiki.biligame.com/images/blhx/7/7e/43etw4yt0bnhkj94ucbw0x2i3eu0odm.mp3", "type": "cheerleader_desc", "scene": "应援啦啦队", "skin": "Champion of Unicorn"},
            {"text": "哥哥辛苦了独角兽优酱光辉姐姐和大家一直在这里等着哥哥哦欸嘿嘿", "url": "https://patchwiki.biligame.com/images/blhx/3/33/467stfcnzwada0hav1lf00w208rjw70.mp3", "type": "cheerleader_home", "scene": "大家等你", "skin": "Champion of Unicorn"}
        ]
        
        self.voice_data = voice_data
        print(f"整理了 {len(self.voice_data)} 条独角兽语音数据")
        print("包含皮肤: 基础、小小的星之歌姬、春之礼、憧憬的约会日、")
        print("          梦想的纯白誓约、天使的My Night、清凉阅读时光、")
        print("          天使的护理时间、Champion of Unicorn等")
        print("包含情感: 害羞、撒娇、开心、紧张、战斗、深情、约会等")
        
    def download_voice_files(self):
        """下载所有语音文件"""
        print("\n📥 开始下载独角兽语音文件...")
        print("=" * 50)
        
        success_count = 0
        
        for i, voice in enumerate(self.voice_data):
            filename = f"unicorn_{voice['type']}_{i+1:02d}.mp3"
            file_path = self.dataset_dir / filename
            
            if file_path.exists():
                print(f"✅ {filename} 已存在")
                success_count += 1
                continue
            
            print(f"\n🔄 下载 {voice['scene']}: {voice['text'][:30]}...")
            
            if self.download_audio_file(voice['url'], str(file_path)):
                success_count += 1
                print(f"✅ {filename} 下载完成")
            else:
                print(f"❌ {filename} 下载失败")
            
            # 添加延迟避免请求过于频繁
            time.sleep(0.5)  # 减少延迟时间
        
        print(f"\n📊 下载结果: {success_count}/{len(self.voice_data)} 成功")
        return success_count
    
    def download_audio_file(self, url, save_path):
        """下载单个音频文件"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://wiki.biligame.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # 检查文件大小
            file_size = Path(save_path).stat().st_size
            if file_size < 1000:  # 小于1KB可能是错误文件
                print(f"   ⚠️ 文件过小: {file_size} bytes")
                Path(save_path).unlink(missing_ok=True)
                return False
            
            print(f"   文件大小: {file_size / 1024:.1f} KB")
            return True
            
        except Exception as e:
            print(f"   下载失败: {e}")
            return False
    
    def convert_to_wav(self):
        """将MP3文件转换为WAV格式（训练需要）"""
        print("\n🔄 转换音频格式为WAV...")
        
        try:
            import subprocess
            
            mp3_files = list(self.dataset_dir.glob("*.mp3"))
            if not mp3_files:
                print("❌ 未找到MP3文件")
                return
            
            converted_count = 0
            for mp3_file in mp3_files:
                wav_file = mp3_file.with_suffix('.wav')
                
                if wav_file.exists():
                    print(f"✅ {wav_file.name} 已存在")
                    continue
                
                try:
                    # 使用ffmpeg转换（如果安装了的话）
                    subprocess.run([
                        'ffmpeg', '-i', str(mp3_file), 
                        '-ar', '44100', '-ac', '1', '-y',  # 44100Hz单声道
                        str(wav_file)
                    ], check=True, capture_output=True)
                    
                    print(f"✅ 转换完成: {wav_file.name}")
                    converted_count += 1
                    
                    # 删除原MP3文件（可选）
                    # mp3_file.unlink()
                    
                except subprocess.CalledProcessError:
                    print(f"❌ 转换失败: {mp3_file.name}")
                except FileNotFoundError:
                    print("❌ 未找到ffmpeg，请先安装")
                    print("   下载地址: https://ffmpeg.org/download.html")
                    break
            
            print(f"📊 转换结果: {converted_count} 个文件")
            
        except ImportError:
            print("⚠️ 需要安装ffmpeg来转换音频格式")
    
    def detect_language(self, text):
        """检测文本语言（中文或日文）"""
        # 统计中文字符
        chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        # 统计日文平假名和片假名
        japanese_count = sum(1 for char in text if
                           ('\u3040' <= char <= '\u309f') or  # 平假名
                           ('\u30a0' <= char <= '\u30ff'))    # 片假名

        # 如果日文字符更多，返回JA，否则返回ZH
        if japanese_count > chinese_count:
            return "JA"
        else:
            return "ZH"

    def save_text_data(self, speaker_name="unicorn"):
        """保存文字数据到文本文件"""
        print("\n📝 保存文字数据...")

        # 保存为JSON格式
        import json
        text_data = []
        for i, voice in enumerate(self.voice_data):
            filename = f"unicorn_{voice['type']}_{i+1:02d}"
            lang = self.detect_language(voice['text'])
            text_data.append({
                'filename': filename,
                'text': voice['text'],
                'scene': voice['scene'],
                'skin': voice['skin'],
                'type': voice['type'],
                'language': lang
            })

        json_file = self.dataset_dir / "text_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(text_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON格式已保存: {json_file}")

        # 保存为纯文本格式（每行一条）
        txt_file = self.dataset_dir / "text_data.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for i, voice in enumerate(self.voice_data):
                filename = f"unicorn_{voice['type']}_{i+1:02d}"
                f.write(f"{filename}|{voice['text']}\n")
        print(f"✅ 文本格式已保存: {txt_file}")

        # 保存为CSV格式
        csv_file = self.dataset_dir / "text_data.csv"
        with open(csv_file, 'w', encoding='utf-8-sig') as f:
            f.write("文件名,文本内容,场景,皮肤,类型,语言\n")
            for item in text_data:
                filename = item['filename']
                text = item['text'].replace('"', '""')  # 转义双引号
                f.write(f'"{filename}","{text}","{item["scene"]}","{item["skin"]}","{item["type"]}","{item["language"]}"\n')
        print(f"✅ CSV格式已保存: {csv_file}")

        # 生成So-VITS-SVC的list文件格式
        list_file = self.dataset_dir / f"{speaker_name}.list"
        with open(list_file, 'w', encoding='utf-8') as f:
            for item in text_data:
                # 格式: dataset/44k/speaker/filename.wav|LANG|text
                wav_path = f"dataset/44k/{speaker_name}/{item['filename']}.wav"
                f.write(f"{wav_path}|{item['language']}|{item['text']}\n")
        print(f"✅ List格式已保存: {list_file}")

        # 统计语言分布
        lang_stats = {}
        for item in text_data:
            lang = item['language']
            lang_stats[lang] = lang_stats.get(lang, 0) + 1

        print(f"\n语言统计:")
        for lang, count in lang_stats.items():
            lang_name = "中文" if lang == "ZH" else "日文"
            print(f"  {lang_name}({lang}): {count} 条")

        return len(text_data)

    def create_dataset_info(self):
        """创建数据集信息文件"""
        info_content = f"""# 独角兽语音数据集

## 数据来源
- 游戏: 碧蓝航线 (Azur Lane)
- 角色: 独角兽 (Unicorn)
- 语言: 中文
- 声优: 上坂すみれ (Uesaka Sumire)

## 数据统计
- 总文件数: {len(self.voice_data)}
- 基础语音: ~32条
- 皮肤语音: ~30条
- 皮肤种类: 10+种不同造型
- 数据类型: 游戏内官方语音
- 音频格式: MP3 -> WAV
- 采样率: 44100Hz
- 声道: 单声道

## 皮肤分类
- 基础形态: 日常对话和战斗语音
- 小小的星之歌姬: 歌手偶像风格
- 春之礼: 春节新年主题
- 憧憬的约会日: 约会恋爱主题
- 梦想的纯白誓约: 婚纱誓约主题
- 天使的My Night: 偶像演出主题
- 清凉阅读时光: 夏日休闲主题
- 天使的护理时间: 护士制服主题
- Champion of Unicorn: 应援啦啦队主题
- 其他特殊皮肤语音

## 文件说明
"""

        for i, voice in enumerate(self.voice_data):
            filename = f"unicorn_{voice['type']}_{i+1:02d}"
            info_content += f"- {filename}: [{voice['skin']}] {voice['scene']} - {voice['text'][:40]}...\n"

        info_file = self.dataset_dir / "README.md"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(info_content)

        print(f"✅ 数据集信息已保存: {info_file}")
    
    def prepare_for_training(self):
        """为训练准备数据集"""
        print("\n🛠️ 准备训练数据集...")
        
        wav_files = list(self.dataset_dir.glob("*.wav"))
        if not wav_files:
            print("❌ 未找到WAV文件，请先完成音频转换")
            return False
        
        print(f"✅ 找到 {len(wav_files)} 个WAV文件")
        print(f"📁 数据集路径: {self.dataset_dir}")
        print(f"🎯 下一步: 运行So-VITS-SVC预处理")
        
        training_commands = f"""
## So-VITS-SVC训练命令

cd {self.base_dir}

# 1. 重采样 (44100Hz -> 44100Hz, 已经是正确格式)
python resample.py

# 2. 生成配置文件
python preprocess_flist_config.py --speech_encoder vec256l9

# 3. 提取特征
python preprocess_hubert_f0.py

# 4. 开始训练
python train.py -c configs/config.json -m 44k
"""
        
        with open(self.base_dir / "training_guide.txt", 'w', encoding='utf-8') as f:
            f.write(training_commands)
        
        print("📝 训练指南已保存: training_guide.txt")
        return True

def main():
    # 设置控制台编码为UTF-8
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("独角兽语音数据爬取器")
    print("=" * 60)

    scraper = UnicornVoiceScraper()

    # 从提供的HTML数据中提取语音信息
    html_content = """你提供的HTML内容..."""  # 这里会使用实际的HTML内容

    # 手动解析提取（因为我们已经有了结构化的数据）
    scraper.extract_voice_data_from_html("")

    print(f"🎯 准备下载到: {scraper.dataset_dir}")
    
    # 确认下载
    confirm = input("是否开始下载独角兽语音文件? (y/n): ").lower().strip()
    if confirm != 'y':
        print("❌ 取消下载")
        return
    
    # 下载语音文件
    success_count = scraper.download_voice_files()
    
    if success_count > 0:
        print(f"\n🎉 成功下载 {success_count} 个语音文件!")

        # 保存文字数据
        text_count = scraper.save_text_data()
        print(f"✅ 已保存 {text_count} 条文字数据")

        # 创建数据集信息
        scraper.create_dataset_info()

        # 转换格式
        print("\n💡 接下来需要:")
        print("1. 安装 ffmpeg (用于音频格式转换)")
        print("2. 运行音频转换: scraper.convert_to_wav()")
        print("3. 开始训练独角兽语音模型")

        # 询问是否转换格式
        convert_confirm = input("\n是否现在转换音频格式为WAV? (需要ffmpeg) (y/n): ").lower().strip()
        if convert_confirm == 'y':
            scraper.convert_to_wav()
            scraper.prepare_for_training()
    
    print("\n" + "=" * 60)
    print("🦄 独角兽专用So-VITS-SVC模型训练数据准备完成!")
    print("现在你可以训练属于自己的独角兽语音模型了!")

if __name__ == "__main__":
    main()