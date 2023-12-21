import discord
from discord.ext import commands
from enum import IntEnum, auto
import random
import asyncio
import csv
import pathlib
import nest_asyncio
nest_asyncio.apply()
# 設定
LimitTime = 300

# 職稱
class Role(IntEnum):
    Master = auto()
    People = auto()
    Insider = auto()

# 遊戲狀態
class GameStatus(IntEnum):
    NotReady = auto()  
    Ready = auto()
    Question = auto()
    Discussion = auto()

    Judge = auto()
    Votiong = auto()

# 暫定答案列表
answers = ['蘋果','大猩猩','香蕉']

#預設答案集
defaultAnswerset = '名詞'


TOKEN = ''

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command("help")

# 成員名單
gamemember = []

# 玩家列表
# 0.discord.Member
# 1.Role
# 2.投票結束 bool
# 3.Judge投票結果 Bool
# 4.Votiong 第二次投票結果 int
currentmember = []

#目前答案集
currentanswerset = ''

#目前答案
currentanswer = ''

#遊戲狀態
currentStatus = GameStatus.NotReady

#回答的人
answerMenber = discord.Member
#遊戲的頻道
GameChannel = discord.TextChannel

#討論時間
RemainTime = 0

def getMasterMember():
    for items in currentmember:
        if items[1] == Role.Master:
            return items[0]
    print("can't find master")

def getInsiderMember():
    for items in currentmember:
        if items[1] == Role.Insider:
            return items[0]
    print("can't find insider")

def getCurentMemberList():
    memberstr = ''
    for index in range(len(currentmember)):
        memberstr = memberstr + '\n' + str(index) + ' : ' + currentmember[index][0].mention
    return memberstr


def getCurentMemberListVoting():
    global answerMenber
    memberstr = ''
    for index in range(len(currentmember)):
        if currentmember[index][1] != Role.Master and currentmember[index][0] != answerMenber:
            memberstr = memberstr + '\n' + str(index) + ' : ' + currentmember[index][0].mention
    return memberstr

def clearVote(): # 清除目前投票
    global currentmember
    for items in currentmember:
        items[2] = False

def loadAnswer(answerFileName:str):
    global answers
    global currentanswerset

    p_abs = pathlib.Path(__file__).parent / pathlib.Path('answer')

    if answerFileName == 'all':  #加載全部
        files = p_abs.glob('*.csv')
        for file in files:
            with open(file,encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    answers.extend(row)
        currentanswerset = 'all'

            
    else: # 個別答案讀取
        answers.clear()

        answerPath = p_abs / pathlib.Path(answerFileName + '.csv')
        with open(answerPath,encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                answers.extend(row)
        
        currentanswerset = answerFileName


@bot.event
async def on_ready():
    # 登入通知
    print('您現在已登入')
    
    loadAnswer(defaultAnswerset)
    synced = await bot.tree.sync()
    print(str(len(synced))+"  com")
    
    pass
@bot.tree.command(name="readyhelp",description="查看準備階段指令")
async def readyhelp(interaction:discord.Interaction):
    embed=discord.Embed(color=0x0080ff,title="準備階段的指令")
    embed.add_field(name="rule" , value="查看遊戲規則", inline=False)
    embed.add_field(name="listanswer", value="查看所有答案庫", inline=False)
    embed.add_field(name="updateanswer", value="更新答案庫", inline=False)
    embed.add_field(name="answerset", value="現在選用答案庫", inline=False)
    embed.add_field(name="join", value="加入遊戲", inline=False)
    embed.add_field(name="remove" , value="離開遊戲", inline=False)
    embed.add_field(name="clear" , value="清空玩家", inline=False)
    embed.add_field(name="members" , value="確認所有參加遊戲玩家", inline=False)
    embed.add_field(name="gamehelp" , value="遊戲開始時所需要的所有指令", inline=False)
    await interaction.response.send_message(embed=embed) 

@bot.tree.command(name="gamehelp",description="查看遊戲階段的指令")
async def gamehelp(interaction:discord.Interaction):
    embed=discord.Embed(color=0x0080ff,title="遊戲階段的指令")
    embed.add_field(name="ready" , value="準備遊戲", inline=False)
    embed.add_field(name="begin" , value="開始遊戲", inline=False)
    embed.add_field(name="answer" , value="輸入答對人的編號", inline=False)
    embed.add_field(name="enddis" , value="跳過討論時間", inline=False)
    embed.add_field(name="end" , value="時間到如果沒有答出答案輸入/end", inline=False)
    embed.add_field(name="judge", value="判斷答對者是不是內幕人士", inline=False)
    embed.add_field(name="vote", value="投誰是內幕人士", inline=False)
    await interaction.response.send_message(embed=embed) 

@bot.tree.command(name="rule",description="遊戲規則")
async def rule(interaction:discord.Interaction): 
    say="〈前言〉\n人，真的能自主、自由的做決定嗎？縱使你做的決定看似自主，但你所做的決定，是否被所聞、所感、所見所影響了？進一步來說，你做決定的過程，是不是不知不覺中被某人操縱了？《局內人遊戲》就是在探討這樣的問題。\n〈陣營介紹〉\n遊戲分為兩個陣營：正方陣營與反方陣營\n～正方陣營～\n主持人：知道正確答案，並且只能根據其他人問的問題回答「是」或「否」。\n一般人：不知道正確答案，跟主持人詢問問題以猜出正確答案。\n～反方陣營～\n內幕人士：你知道正確答案，但請隱匿自己的身份。你的勝利條件是要引導一般人問到主持人知道的正確答案，且不能被大家指認出來。\n〈遊戲階段〉\n～玩家報名階段～\n輸入指定指令，以加入遊戲。\n～玩家確認階段～\n當所有玩家加入遊戲後，便可以輸入指定指令，確定玩家名單。\n～角色隨機分配階段～輸入指定指令，系統會隨機幫大家分配角色，訊息會以私訊形式傳送，請注意私訊！\n～討論階段～\n大家隨意提問，由主持人回答是或否。\n～答案判斷階段～\n主持人根據最終的答案，判斷是否猜到正確答案\n～第一階段指認內幕人士～\n全體（包含主持人）投票，指認猜出答案的人是否為內幕人士。\n～第二階段指認內幕人士～\n當被猜出答案的人並非為內幕人士，進行第二次投票，指認內幕人士。\n～結局～\n根據勝利條件，決定勝利方。\n〈勝利條件〉\n正方陣營：讓正確答案被主持人以外的任何人猜出且指認出內幕人士\n反方陣營：讓正確答案被主持人以外的任何人猜出且不能被指認出\n*注意：如果正確答案沒有被猜出，是所有人的失敗！"
    say+="\n利用readyhelp來查看準備階段的指令 利用gamehelp來查看準備階段的指令"
    await interaction.response.send_message(say)

# 答案庫更新
@bot.tree.command(name="updateanswer",description="更新答案庫")
async def updateanswer(interaction:discord.Interaction,filename:str): 
    try:
        loadAnswer(str(filename))
        await interaction.response.send_message(f'已將答案庫更新為{str(filename)}')
    except:
        await interaction.response.send_message(f'找不到{filename}')

# 答案庫顯示
@bot.tree.command(name="listanswer",description="庫存答案庫")
async def listanswer(interaction:discord.Interaction): 
    p_abs = pathlib.Path(__file__).parent / pathlib.Path('answer')
    files = p_abs.glob('*.csv')
    aw=""
    for file in files:
        aw+=(f'{file.name.rstrip(".csv")}\n')
    await interaction.response.send_message(aw)

@bot.tree.command(name="answerset",description="查看答案庫")
async def answerset(interaction:discord.Interaction): 
    await interaction.response.send_message(f'現在答案庫為 {currentanswerset} ')

#新增玩家
@bot.tree.command(name="join",description="加入遊戲")
async def join(interaction:discord.Interaction,member:discord.User): 
    if member not in gamemember:
        gamemember.append(member)
        await interaction.response.send_message('{} 加入遊戲! '.format(member.display_name))
    else:
        await interaction.response.send_message('{} 已在遊戲內! '.format(member.display_name))

# 玩家刪除
@bot.tree.command(name="remove",description="退出遊戲")
async def remove(interaction:discord.Interaction,member:discord.User): 
    if member in gamemember:
        gamemember.remove(member)
        await interaction.response.send_message('{} 退出遊戲!'.format(member.display_name))
    else:
        await interaction.response.send_message('{} 尚未加入遊戲! '.format(member.display_name))
# 清空玩家
@bot.tree.command(name="clear",description="清空玩家")
async def clear(interaction:discord.Interaction): 
    gamemember.clear()
    await interaction.response.send_message('玩家已全部刪除')

# 玩家確認
@bot.tree.command(name="members",description="確認玩家")
async def members(interaction:discord.Interaction): 
    memberstr = ''
    for item in gamemember:
        memberstr = memberstr + '\n' + item.display_name
    await interaction.response.send_message('-Members-\n {0}'.format(memberstr))

# 遊戲準備
@bot.tree.command(name="ready",description="準備遊戲")
async def ready(interaction:discord.Interaction): 
    global currentStatus
        

    if currentStatus != GameStatus.NotReady:
        await interaction.response.send_message('錯誤：遊戲尚未準備')
        return

    # 角色分配
    # Master(主持人)
    MasterIdx = random.randint(0,len(gamemember)-1)

    # Insider(內幕人士)
    while True:
        InsiderIdx = random.randint(0,len(gamemember)-1)
        if MasterIdx != InsiderIdx:
            break

    #currentmember初始化
    global currentmember
    currentmember.clear()
    role = Role.People

    for index in range(len(gamemember)):
        if index == MasterIdx:
            role = Role.Master
        elif index == InsiderIdx:
            role = Role.Insider
        else:
            role = Role.People

        currentmember.append([gamemember[index],role,False,False,0])

    # 抽答案
    global currentanswer
    currentanswer = answers[random.randint(0,len(answers)-1)]
    await interaction.response.send_message("請準備查看dm")
    # 向各自DM傳訊息
    for index in range(len(currentmember)):

        if currentmember[index][1] == Role.Master:
            rolestr = '主持'
            ansstr = '答案是『' + currentanswer + '』'
            
        elif currentmember[index][1] == Role.Insider:
            rolestr = '內幕人士'
            ansstr = '答案是『' + currentanswer + '』'
            
        else:
            rolestr = '一般人'  
            ansstr = '請猜出答案！'    
        
        sendstr =  currentmember[index][0].display_name + '的角色是『' + rolestr + '』\n'
        sendstr = sendstr + ansstr

        dm = await currentmember[index][0].create_dm()
        await dm.send(f"{sendstr}")

    # 遊戲結束通知
    memberstr = getCurentMemberList()
    readystr = '以下成員準備進入遊戲。\n\n' 
    readystr = readystr +  memberstr + '\n 發放遊戲編號。\n\n'
    readystr = readystr + '已透過 DM 將角色寄給大家。 請確認。 \n *也請主持和內幕人士檢查答案。\n\n'
    readystr = readystr +  '使用『/begin』開始遊戲。'
    await interaction.channel.send(f'{readystr}')

  
    currentStatus = GameStatus.Ready


# 遊戲開始
@bot.tree.command(name="begin",description="開始遊戲")
async def begin(interaction:discord.Interaction): 
    global GameChannel
    global currentStatus

    if currentStatus != GameStatus.Ready:
        await interaction.response.send_message('錯誤：尚未準備好')
        return

    GameChannel = interaction.channel
    mastermember = getMasterMember()

    startstr = '遊戲開始！\n\n'
    startstr = startstr + '主持是:' + mastermember.mention + '\n'
    startstr = startstr + mastermember.mention + '請開始問問題並猜出答案！\n\n'
    
    memberstr = getCurentMemberList()

    startstr = startstr + '當您得到答案時，請輸入「/answer 答對人的遊戲編號」。\n\n' + memberstr
    startstr = startstr + '\n時間限制為' + str(LimitTime) + '秒'
    await interaction.response.send_message(f'{startstr}')

    secs = 1
    
    global RemainTime
    RemainTime = 0
    
    currentStatus = GameStatus.Question

    for i in range(LimitTime):
        await asyncio.sleep(secs)
        RemainTime = RemainTime + secs
        if LimitTime - i == LimitTime/2:
            await interaction.channel.send(f'剩下{LimitTime/2}秒')
        elif LimitTime - i == LimitTime/5:
            await interaction.channel.send(f'剩下{LimitTime/5}秒')
        elif LimitTime - i == 10:
            await interaction.channel.send(f'剩下10秒')
        
        if currentStatus != GameStatus.Question:
            break
    

    if currentStatus == GameStatus.Question: 
        timeupstr = 'TimeUp！\n\n'
        timeupstr = timeupstr + '如果您在最後一刻得到答案\n\t→請輸入「/answer 答對人的遊戲編號」'
        timeupstr = timeupstr + '如果沒有找到答案\n\t→請輸入「/end」'

        await interaction.channel.send(f'{timeupstr}')


@bot.tree.command(name="end",description="時間到如果沒有答出答案")
async def end(interaction:discord.Interaction): 
    if currentStatus != GameStatus.Question:
        await interaction.response.send_message('錯誤：現在不是提問的時間')
        return
    await endResult(False,False)

#回答
@bot.tree.command(name="answer",description="輸入答對人的編號")
async def answer(interaction:discord.Interaction,id:int): 
    global answerMenber
    global currentStatus

    if currentStatus != GameStatus.Question:
        await interaction.response.send_message('錯誤：未準備好')
        return
    try:
        if currentmember[int(id)][1] ==  Role.Master:
            await interaction.response.send_message('錯誤:主持人不能是答對者')
            return
        
    
        answerMenber = currentmember[int(id)][0]
        
        answerstr = answerMenber.mention + '給了一個很接近的答案。\n'
        answerstr = answerstr + '等一下！'+ answerMenber.mention + '可能是內幕人士\n'
        answerstr = answerstr + '那裡可能還有其他可疑人員。 讓我們大家回顧一下，思考一下。\n\n'
        answerstr = answerstr + '如果你提前完成複習，也可以用「/enddis」跳過。\n'
        answerstr = answerstr + '限制時間為:' + str(RemainTime) + '秒'
        await interaction.response.send_message(f'{answerstr}')

        currentStatus = GameStatus.Discussion

        await asyncio.sleep(RemainTime)

        if currentStatus == GameStatus.Discussion: # 終止還在進行的討論
            await jadgeAnnounce()
    except:
        await interaction.response.send_message("找不到遊戲編號{}".format(id))

#收尾
@bot.tree.command(name="enddis",description="跳過討論時間")
async def enddis(interaction:discord.Interaction):
    await interaction.response.send_message("成功跳過!")
    await jadgeAnnounce()


async def jadgeAnnounce():
    global currentStatus

    if currentStatus != GameStatus.Discussion:
        await GameChannel.send('錯誤：討論尚未完成。')
        return

    disstr = '除了回答者之外的所有人，請投票決定' + str(answerMenber.mention) + '是否為內幕人士\n\n'
    await GameChannel.send(f'{disstr}')
    
    clearVote()

    #寄信到各自的DM
    jadgedmstr = '您認為'+answerMenber.display_name + '是內幕人士嗎？\n'
    jadgedmstr = jadgedmstr + '請透過在下面留言來投票。\n\n'
    jadgedmstr = jadgedmstr + '答對者為內幕人士\n'
    jadgedmstr = jadgedmstr + '\t→「/judge true」\n'
    jadgedmstr = jadgedmstr + '答對者並非內幕人士\n'
    jadgedmstr = jadgedmstr + '\t→「/judge false」\n'
    for index in range(len(currentmember)):
        if currentmember[index][0] != answerMenber: #向回答者以外的人DM寄信
            dm = await currentmember[index][0].create_dm()
            await dm.send(f"{jadgedmstr}")

    currentStatus = GameStatus.Judge



@bot.tree.command(name="judge",description="答對者是不是內幕人士")
async def judge(interaction:discord.Interaction,answer:bool):
    global currentStatus

    if currentStatus != GameStatus.Judge:
        await GameChannel.send('錯誤：不是投票時間')
        return
    if answer==True:
        isInsider = True
    else:
        isInsider = False

    for item in currentmember:
        if interaction.user == item[0]:
            item[3] = isInsider
            item[2] = True
            break
    await interaction.response.send_message("投票成功")
    await GameChannel.send(f'{interaction.user.display_name} 投票完成')

    Sended = True
    
    #投票結束確認
    for items in currentmember:
        if items[0] != answerMenber:
            # Sended = Sended and items[2]
            Sended = Sended and items[2]

    if Sended:
        #投票結束
        await resultJadge()

# 回答者＝內幕人士的投票結果
async def resultJadge():
    global currentStatus

    resultstr = '大家的投票已經完成\n\n'
    resultstr = resultstr + '<投票結果>\n'

    result = ''
    vote = ''
    voteInsider = 0
    voteNotInsider = 0
    for items in currentmember:
        if items[0] != answerMenber:
            if items[3]:
                vote = 'Y'
                voteInsider = voteInsider + 1
            else:
                vote = 'N'
                voteNotInsider = voteNotInsider + 1

            result = result + items[0].display_name + ' : ' + vote + '\n'

    resultstr = resultstr + result 
    resultstr = resultstr + '\n <合計>\n'
    resultstr = resultstr + '內幕人士：' + str(voteInsider) + '\n'
    resultstr = resultstr + '不是內幕人士: ' + str(voteNotInsider) + '\n\n'

    if voteInsider > voteNotInsider:
        resultstr = resultstr + '經過多數投票，大家認為:' + answerMenber.display_name + '是內幕人士\n'
        expectInsider = True
    else:
        resultstr = resultstr + '經過多數投票，大家認為:' + answerMenber.display_name + '不是內幕人士\n'
        expectInsider = False
        
    
    resultstr = resultstr + answerMenber.display_name + '\n'
    await GameChannel.send(f'{resultstr}')

    for index in range(3):
        await GameChannel.send('...')
        await asyncio.sleep(1)
        index
    

    for items in currentmember:
        if items[0] == answerMenber:
            if items[1] == Role.Insider:
                isInsider = True
            else:
                isInsider = False
            break
    
    if isInsider:
        resultstr = answerMenber.display_name + '是內幕人士！\n'
        await GameChannel.send(f'{resultstr}')
        if expectInsider:
            await endResult(False,True)
        else:
            await endResult(True,True)
    else:
        resultstr = '不是內幕人士！\n' 
        await GameChannel.send(f'{resultstr}')
        if expectInsider:
            await endResult(True,True)
        else:
            await voteAnnounce()
            
    

#投票宣告
async def voteAnnounce():
    global currentStatus
    resultstr = '那誰是內幕人士呢？ 請透過DM投票。\n'
    await GameChannel.send(f'{resultstr}')

    resultstr = '其中誰是內幕人士？\n'
    resultstr = resultstr + getCurentMemberListVoting()
    resultstr = resultstr + '\n'
    resultstr = resultstr + '請透過向我的 DM 寄信以回覆\n\n'
    resultstr = resultstr + '/vote 遊戲編號\n'

    for index in range(len(currentmember)):
        dm = await currentmember[index][0].create_dm()
        await dm.send(f"{resultstr}")    
    
    clearVote()
    currentStatus = GameStatus.Votiong

@bot.tree.command(name="vote",description="投誰是內幕人士")
async def vote(interaction:discord.Interaction,id:int):
    arg=int(id)
    global currentStatus

    if currentStatus != GameStatus.Votiong:
        await GameChannel.send('錯誤：現在不是投票時間')
        return
    
    for items in currentmember:
        if items[0] == interaction.user:
            items[4] = int(arg)
            items[2] = True
    await interaction.response.send_message("投票成功")
    await GameChannel.send(f'{interaction.user.display_name} 投票結束')

    Sended = True
    
    #投票結束確認
    for items in currentmember:
        Sended = Sended and items[2]

    if Sended:
        #投票結束
        await resultVote()


    

async def resultVote():
    resultstr = '大家已經完成投票\n\n'

    resultstr = resultstr + '<投票結果>\n'

    result = [] 

    for index in range(len(currentmember)):
        result.append(0)
    
    votestr = ''

    for index in range(len(currentmember)):
        votestr = votestr + currentmember[index][0].display_name + ' : ' + currentmember[currentmember[index][4]][0].display_name + '\n'
        result[currentmember[index][4]] = result[currentmember[index][4]] + 1

    resultstr = resultstr + votestr

    resultstr = resultstr + '\n <合計>\n'

    totalstr = ''
    for index in range(len(result)):
        totalstr = totalstr + currentmember[index][0].display_name + ' : ' + str(result[index]) + '\n'

    resultstr = resultstr + totalstr

    maxcount = 0 
    max_memberindex = 0

    for index in range(len(result)):
        if result[index] == max(result):
            maxcount = maxcount + 1
            max_memberindex = index

    expectMember = discord.Member

    resultstr = resultstr + '\n'

    if maxcount == 1: #最多票的人只有一個
        expectMember = currentmember[max_memberindex][0]
        resultstr = resultstr + '得票最多的人是:' + expectMember.display_name + '\n'
    else: #最多票的人有很多個
        for item in currentmember:
            if item[0] == answerMenber:
                expectMember = currentmember[item[4]][0]
                break

        resultstr = resultstr + '由於投票數最多的人有多個，因此回答者' + expectMember.display_name + '將是投票數最多的人\n'
    
    resultstr = resultstr + expectMember.display_name 
    await GameChannel.send(f'{resultstr}')


    for index in range(3):
        await GameChannel.send('...')
        await asyncio.sleep(1)
        index

    for item in currentmember:
        if item[0] == expectMember:
            if item[1] == Role.Insider:
                await GameChannel.send(f'就是內幕人士！\n')
                await endResult(False,True)
                
            else:
                await GameChannel.send(f'不是內幕人士！\n') 
                await endResult(True,True)

#結果階段
async def endResult(isWonInsider:bool,isElucidation:bool):

    global currentStatus

    str = '遊戲結束\n\n'
    if isWonInsider:
        str = str + '內幕人士獲勝！\n\n'
    else:
        str = str + '主持人＆一般人獲勝！\n\n'
    

    memstr = ''

    for items in currentmember:
        if items[1] == Role.Insider:
            rolename = '內幕人士'
        elif items[1] == Role.Master:
            rolename = '主持人'
        else:
            rolename = '一般人'
        
        memstr = memstr + items[0].mention + ' : ' + rolename + '\n'

    str = str + memstr + '\n'
    str = str + '答案:『' + currentanswer + '』\n\n'
    str = str + '重置遊戲。\n'
    str = str + '當您準備好下一場比賽時，選擇「/ready」'

    await GameChannel.send(f'{str}')

    currentStatus = GameStatus.NotReady


bot.run(TOKEN)
