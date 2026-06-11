"""
生成纤维素乙醇汇报讲义Word文档（15分钟精简版）

李文煜 1120233042
"""

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "presentation", "讲义.docx")
JIEGAN_IMG = os.path.join(os.path.dirname(__file__), "presentation", "assets", "images", "refs", "jiegan.png")

doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

for i in range(1, 4):
    hs = doc.styles[f'Heading {i}']
    hs.font.name = '微软雅黑'
    hs.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    hs.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
doc.styles['Heading 1'].font.size = Pt(18)
doc.styles['Heading 2'].font.size = Pt(15)
doc.styles['Heading 3'].font.size = Pt(13)

for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)


def p(text, bold=False, italic=False, size=None, align=None, color=None, sb=0, sa=6):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = color
    if align: para.alignment = align
    para.paragraph_format.space_before = Pt(sb)
    para.paragraph_format.space_after = Pt(sa)
    return para


def rp(segments, sb=0, sa=6):
    para = doc.add_paragraph()
    for text, bold, italic, color in segments:
        run = para.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = '微软雅黑'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        run.font.size = Pt(11)
        if color: run.font.color.rgb = color
    para.paragraph_format.space_before = Pt(sb)
    para.paragraph_format.space_after = Pt(sa)
    return para


def core(text):
    """每节核心点，蓝色加粗"""
    rp([(text, True, False, RGBColor(0x1A, 0x23, 0x7E))], sb=4, sa=8)


def fig(title, desc):
    """图解说明：灰色斜体标题+正文描述"""
    para = doc.add_paragraph()
    r1 = para.add_run(f'[{title}] ')
    r1.bold = True; r1.italic = True
    r1.font.name = '微软雅黑'; r1.font.size = Pt(11)
    r1._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    r1.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    r2 = para.add_run(desc)
    r2.font.name = '微软雅黑'; r2.font.size = Pt(11)
    r2._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(4)


def sep():
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run('—' * 40)
    run.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
    run.font.size = Pt(10)
    para.paragraph_format.space_before = Pt(4)
    para.paragraph_format.space_after = Pt(4)


# ===================== 正文 =====================

p('纤维素乙醇产业化投资评估', bold=True, size=22, align=WD_ALIGN_PARAGRAPH.CENTER, sb=60, sa=12, color=RGBColor(0x1A, 0x23, 0x7E))
p('汇 报 讲 义', bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, sa=20, color=RGBColor(0x1A, 0x23, 0x7E))
p('李文煜  1120233042', size=12, align=WD_ALIGN_PARAGRAPH.CENTER, sa=6)
p('讲解时间约 15 分钟', size=10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, sa=40, color=RGBColor(0x88, 0x88, 0x88))
sep()

# ===== 开场 =====
doc.add_heading('开场', level=2)
p('大家好，我是李文煜。今天汇报的题目是"纤维素乙醇产业化投资评估"。')
p('核心问题只有一个：纤维素乙醇在实验室里早就"基本可行"了，为什么五十年过去，全世界还没有一座工厂能持续盈利？')
p('汇报分两部分：前8到10分钟讲背景和技术原理，后5到7分钟做投资角色模拟。')
sep()

# ===== Part 1 =====
doc.add_heading('Part 1：背景与技术（8-10分钟）', level=1)

# 节点1
doc.add_heading('一、纤维素乙醇与木质纤维素的顽抗性', level=2)
core('核心点：难在"顽抗性"——beta键结晶+木质素三维交联+LCC共价键，三重防御把糖锁死。')

p('纤维素乙醇用秸秆、木屑等农林废弃物当原料，不与粮食争地。中国年产约8亿吨秸秆。但秸秆里的糖被"锁"住了——木质纤维素是一种天然复合材料：')

rp([('纤维素（40%-60%）', True, False, None), ('：葡萄糖通过beta-1,4-糖苷键连成的直链。注意是"beta"——淀粉里是alpha键，酶很容易切；beta键让相邻葡萄糖旋转180度，直链之间大量氢键平行堆叠，形成致密结晶区，酶进不去。', False, False, None)])
rp([('半纤维素（20%-40%）', True, False, None), ('：木糖等杂糖的支链多糖，结构松散，但通过酯键和醚键与木质素形成LCC复合体，充当"胶水"。', False, False, None)])
rp([('木质素（15%-30%）', True, False, None), ('：三种酚醇单体自由基聚合的三维交联网络。它干三件事：物理包裹（像水泥封砖块）、疏水阻挡、以及最阴险的——非生产性吸附酶分子，酶粘上去就废了。', False, False, None)])

p('这三层交织就是"顽抗性"（Recalcitrance）——植物数亿年进化出的抗降解防御。不打破它，酶碰不到里面的糖。')

sep()

# 节点2
doc.add_heading('二、全球现状与经济性框架', level=2)
core('核心点：理论MESP 2.15美元/加仑，实际3.0-4.5美元——差距来自五个环节的耦合放大效应。')

p('全球生物乙醇280亿加仑/年，纤维素乙醇不到1%。2011年NREL建立了TEA标准框架——用Aspen Plus模拟整座工厂，假设10%内部收益率，倒推最低乙醇售价MESP。理论最优2.15美元/加仑，实际工厂3.0-4.5美元。')

p('差距的根源是"耦合效应"：不是某一个环节差，而是五个环节的效率损失沿产业链级联放大——预处理差10%导致酶解糖产率降更多（非线性），糖浓度低导致乙醇浓度跌破4%的蒸馏阈值，蒸馏能耗指数级上升。')

sep()

# 节点3
doc.add_heading('三、中国的资源与困境', level=2)
core('核心点：8亿吨秸秆资源丰富，但堆积密度极低+季节性强+分布分散，物流成本是致命瓶颈。')

if os.path.exists(JIEGAN_IMG):
    para_img = doc.add_paragraph()
    para_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_img = para_img.add_run()
    run_img.add_picture(JIEGAN_IMG, width=Inches(5.5))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run('图：中国各省份秸秆资源分布及作物构成')
    cr.font.size = Pt(9); cr.font.color.rgb = RGBColor(0x66,0x66,0x66)
    cr.font.name = '微软雅黑'; cr._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

p('从图上可以看到，秸秆高度集中在东北、华北主产区。工厂必须建在50公里半径内，否则运输成本超过原料价值。堆积密度只有50-120 kg/m3，一卡车满载体积才装2吨。产出高度季节性（秋收后1-2个月），需大型仓储。加上酶制剂被外企垄断、单厂投资20亿人民币、缺乏强制掺混政策——产业化步履维艰。')

sep()

# 节点4
doc.add_heading('四、预处理：打破分子屏障', level=2)
core('核心点：EA/ELLA氨处理能把纤维素从晶型I转成晶型III（更松散），但放大150倍后非牛顿流体出现搅拌死区——这是Abengoa和DuPont失败的主因。')

p('预处理占成本18%-20%，任务是打破顽抗性。四种主流方法：稀酸（催化断裂半纤维素糖苷键，但产生糠醛/HMF/乙酸等抑制物）；蒸汽爆破（瞬间泄压机械撕裂纤维）；AFEX→EA→ELLA氨处理路线——氨渗入结晶区打断氢键，触发Cellulose I→III晶型转变（分子间距更大、更易酶解），同时萃取木质素。从AFEX到ELLA，酶用量降40%以上。')

fig('指EA预处理SEM对比图', '左边是未处理的木质纤维素——致密、封闭的结构；右边是EA处理后的——变成多孔蜂窝状，纤维结构被打开，比表面积大幅增加。这就是纤维素可及性提升2倍的直观证据。')
fig('指ELLA成分变化图', '横轴是预处理时间0到120小时。随时间延长，木聚糖（半纤维素的主要成分）从22%降到接近0——说明半纤维素被有效溶出；葡聚糖（纤维素）稳定在30%——说明纤维素没被破坏；而不溶性木质素占比从17%升到40%——是因为半纤维素被去除了，木质素相对富集。')

p('但放大效应是致命的：工业规模下高固含率料浆变成非牛顿流体，粘度剧增，搅拌器出现"死区"——某些角落物料几乎不流动，预处理效果远低于设计值。Abengoa 2016年破产、DuPont 2017年出售装置，都跟这个有关。')

sep()

# 节点5
doc.add_heading('五、酶解：成本黑洞', level=2)
core('核心点：纤维素酶比淀粉酶贵10倍——需要三种酶协同"爬行"切割结晶底物，且无商业化回收方案。')

p('纤维素酶成本0.30-0.50美元/加仑，淀粉酶只要0.03美元。原因：纤维素是固态结晶底物，需要三种酶组成系统——内切酶（EG）在无定形区随机切割创造链端；外切酶（CBH）从链端沿纤维素链"爬行"，每次切下一个纤维二糖，速率只有几个葡萄糖/秒；beta-葡萄糖苷酶（BGL）把纤维二糖切成葡萄糖，否则纤维二糖积累会反过来抑制CBH。')

fig('指酶解工艺流程图', '展示了四种工艺配置：最基础的是分步水解发酵（SHF）——先水解再发酵，两个罐分开；进一步是同步水解发酵（SSF）——水解和发酵在同一个罐里同时进行；再进一步是共发酵——预处理浆料和预处理液一起进罐，五碳糖六碳糖同时发酵；最整合的是把酶生产、水解、发酵全塞进一个罐。整合程度越高，设备投资越少，但控制难度越大。')

p('三种酶回收路线（固定化、温敏聚合物、原位真空蒸馏）都没有走出实验室。这是产业最大的技术空白。')

sep()

# 节点6
doc.add_heading('六、发酵：五碳糖利用', level=2)
core('核心点：改造酵母吃木糖的两条路线都有原理性缺陷（辅酶不平衡/可逆反应），加上乙酸的ATP竞争直接瘫痪木糖代谢。')

p('水解液中30%-40%是木糖，传统酵母不能用——三分之一碳源浪费。两条改造路线：XR-XDH（两步氧化还原，但XR偏好NADPH、XDH偏好NAD+，辅酶不平衡导致木糖醇积累堵路）；XI（一步异构，不耗辅酶，但可逆反应平衡偏向木糖侧85:15，需下游拉动）。')

fig('指代谢工程路径图', '展示了从乙酰辅酶A出发的多步酶促反应路径，涉及来自不同物种（酿酒酵母、梭菌、大肠杆菌）的9个外源基因。不同基因组合（XA-1到XA-6菌株）的正丁醇产量差异巨大——XA-3和XA-4达到7 mg/L以上，而缺失关键酶EcEutE的XA-5和XA-6几乎不产。这说明代谢工程中酶的组合搭配极为关键，不是把基因堆进去就行。')
fig('指乙酸盐浓度影响图', '横轴是乙酸盐浓度，纵轴是发酵产物产量。存在一个最优点——约0.2 g/L时产量最高，超过这个浓度产量反而下降。这与前面讲的抑制物机制一致：低浓度乙酸可能作为碳源被利用，但高浓度就会酸化胞质、消耗ATP，抑制发酵。')

p('更关键的是抑制物：乙酸穿透细胞膜酸化胞质，酵母被迫消耗ATP排H+，而木糖代谢本身就产能少，被乙酸一抢ATP直接瘫痪。糠醛消耗NAD(P)H扰乱辅酶池，酚类破坏膜完整性。协同毒害下，工业木糖发酵率只有葡萄糖的1/5到1/10。')

sep()

# 节点7
doc.add_heading('七、计算机交叉赋能', level=2)
core('核心点：TEA识别模型美化、ML优化多维参数、LCA量化115%减排溢价、GIS优化供应链选址。')

rp([('TEA', True, False, None), ('——不只算MESP，更重要的是敏感性分析，识别"杠杆点"和"美化工具"。', False, False, None)])
rp([('ML', True, False, None), ('——十几个耦合参数的空间里，用随机森林/神经网络学习参数到产率的映射，快速搜索最优工艺窗口。', False, False, None)])
rp([('LCA', True, False, None), ('——全生命周期追踪排放。减排115%超过100%是因为秸秆不利用也会腐烂产甲烷（温室效应是CO2的28倍），在碳交易市场有额外收入。', False, False, None)])
rp([('GIS', True, False, None), ('——整合秸秆分布、公路网络、运输成本的空间数据，运筹学模型优化工厂选址。', False, False, None)])

sep()

# 节点8
doc.add_heading('八、核心结论', level=2)
core('核心点：不是"技术不行"，是"系统集成不行"——木桶效应+五层耦合放大。')

p('五环节成熟度：原料85、蒸馏80、预处理75、发酵65、酶解40。酶解是最短板。更致命的是耦合效应：预处理↓ → 可及性非线性↓ → 糖产率↓ → 乙醇<4% → 蒸馏能耗指数↑。五层效率损失相乘，实际MESP远高于理论值。')
rp([('结论：从"技术可行"到"系统可行"的鸿沟，才是真正的挑战。', True, False, None)])

sep()

# ===== Part 2 =====
doc.add_heading('Part 2：角色模拟（5-7分钟）', level=1)
p('你是一位管理10亿美元的清洁技术风投。"绿源生物科技"寻求C轮5000万美元，声称10吨/天中试装置实现85%理论产率、MESP 1.80美元/加仑，要建5万吨/年商业化工厂。你要问五个穿透性问题：')

sep()

doc.add_heading('问题一：预处理放大', level=2)
rp([('"10吨/天到1500吨/天，均匀性怎么保证？"', True, False, None)])
rp([('失败模式：链式崩溃。', True, False, None), (' 预处理↓10-15% → 糖产率↓ → 乙醇<4% → MESP从1.80飙到3.00+。Abengoa和DuPont就这么倒的。', False, False, None)])

sep()

doc.add_heading('问题二：酶回收效率', level=2)
rp([('"高固含率下酶回收率能维持多少？"', True, False, None)])
rp([('失败模式：定时炸弹。', True, False, None), (' 回收率80%→40%以下 → 酶成本从0.10回到0.40+美元/加仑 → 利润被吞噬，酶成本变成不可控黑箱。', False, False, None)])

sep()

doc.add_heading('问题三：木糖真实产率', level=2)
rp([('"工业水解液中木糖发酵率到底多少？"', True, False, None)])
rp([('失败模式：双重打击。', True, False, None), (' 乙酸消耗ATP瘫痪木糖代谢 → 利用率85%→50%以下 → 每年损失5000万原料+废水超标，原料利用和环保双失败。', False, False, None)])

sep()

doc.add_heading('问题四：MESP假设', level=2)
rp([('"1.80美元的MESP用的什么假设？"', True, False, None)])
rp([('失败模式：自我欺骗。', True, False, None), (' 低估酶成本、高估折旧年限 → 行业合理假设重算MESP涨到2.50-3.00美元，玉米乙醇市价才1.70。', False, False, None)])

sep()

doc.add_heading('问题五：原料供应链', level=2)
rp([('"有长期秸秆收购协议吗？"', True, False, None)])
rp([('失败模式：无米之炊。', True, False, None), (' 投产推高秸秆价格200→400+元/吨或遇歉收年 → 工厂停产。多家工厂不是技术失败，而是收不到秸秆。', False, False, None)])

sep()

doc.add_heading('投资建议', level=2)
rp([('不建议投资——除非提供：', True, False, None)])
doc.add_paragraph('100吨/天以上中试装置连续运行3个月的稳定数据', style='List Number')
doc.add_paragraph('第三方独立验证酶回收率和五碳糖利用率', style='List Number')
doc.add_paragraph('NREL标准假设重算MESP并提交过程模拟文件', style='List Number')
doc.add_paragraph('已签署的秸秆长期收购协议', style='List Number')
rp([('全部满足后才考虑', False, False, None), ('里程碑式分期注资', True, False, None), ('——达到一个里程碑给一笔。', False, False, None)])

sep()

doc.add_heading('总结', level=2)
rp([('木桶效应', True, False, None), ('——酶解是最大短板，决定系统天花板。', False, False, None)])
rp([('计算机赋能', True, False, None), ('——TEA/ML/LCA/GIS是穿透学术泡沫的分析工具，不是锦上添花。', False, False, None)])
rp([('核心洞察', True, False, None), ('——困境不是"技术不行"而是"系统集成不行"。环境生物技术的成功取决于工程放大、经济可行性和系统思维的协同。', False, False, None)])
p('我的汇报到此结束，谢谢大家。', sb=12)

sep()
p('时长参考（总计约15分钟）：', bold=True, size=10, color=RGBColor(0x88,0x88,0x88))
p('Part 1 背景与技术：约8-10分钟', size=10, color=RGBColor(0x88,0x88,0x88))
p('Part 2 角色模拟：约5-7分钟', size=10, color=RGBColor(0x88,0x88,0x88))

doc.save(OUTPUT_PATH)
print(f"Word讲义已生成: {OUTPUT_PATH}")
