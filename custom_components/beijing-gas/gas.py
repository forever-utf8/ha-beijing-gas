import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

WEEK_QRY_URL = "https://zt.bjgas.com/bjgas-server/i/api/intelligent/getWeekQry?userCode="
STEP_QRY_URL = "https://zt.bjgas.com/bjgas-server/r/api?sysName=CCB&apiName=CM-MOB-IF07"
YEAR_QRY_URL = "https://zt.bjgas.com/bjgas-server/i/api/intelligent/getYearQry?userCode="
USER_INFO_URL = "https://zt.bjgas.com/bjgas-server/i/api/intelligent/queryUserInfo?userCode="

type UserData = dict[str, str | float | int | list[dict]]
type Payload = dict[str, UserData]


class GASData:
    def __init__(self, session, token: str, user_code: str) -> None:
        self._session = session
        self._token = token
        self._user_code = user_code
        self._info: Payload = {}

    def common_headers(self) -> dict[str, str]:
        return {
            "Host": "zt.bjgas.com",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "zh-cn, zh-Hans; q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.7(0x1800072c) "
            "NetType/WIFI Language/zh_CN",
            "Connection": "keep-alive",
            "Authorization": f"Bearer {self._token}",
        }

    async def async_get_week(self, user_code: str) -> None:
        async with self._session.get(WEEK_QRY_URL + user_code, headers=self.common_headers(), timeout=10) as response:
            result = await response.json(content_type=None)
        self._info[user_code]["daily_bills"] = result["rows"][0]["infoList"]

    async def async_get_year(self, user_code: str) -> None:
        async with self._session.get(YEAR_QRY_URL + user_code, headers=self.common_headers(), timeout=10) as response:
            result = await response.json(content_type=None)
        self._info[user_code]["monthly_bills"] = result["rows"][0]["infoList"]

    async def async_get_userinfo(self, user_code: str) -> None:
        async with self._session.get(USER_INFO_URL + user_code, headers=self.common_headers(), timeout=10) as response:
            result = await response.json(content_type=None)
        data = result["rows"][0]
        self._info[user_code]["last_update"] = data["fiscalDate"]
        self._info[user_code]["balance"] = float(data["remainAmt"])
        self._info[user_code]["battery_voltage"] = float(data["batteryVoltage"])
        self._info[user_code]["current_price"] = float(data["gasPrice"])
        self._info[user_code]["month_reg_qty"] = float(data["regQty"])
        self._info[user_code]["mtr_status"] = data["mtrStatus"]

    async def async_get_step(self, user_code: str) -> None:
        headers = self.common_headers() | {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "file://",
        }
        body = {"CM-MOB-IF07": {"input": {"UniUserCode": user_code}}}
        async with self._session.post(STEP_QRY_URL, headers=headers, json=body, timeout=10) as response:
            result = await response.json(content_type=None)

        data = result["soapenv:Envelope"]["soapenv:Body"]["CM-MOB-IF07"]["output"]
        step1_leftover = float(data["Step1LeftoverQty"])
        match step1_leftover > 0:
            case True:
                self._info[user_code]["current_level"] = 1
                self._info[user_code]["current_level_remain"] = step1_leftover
            case False:
                self._info[user_code]["current_level"] = 2
                self._info[user_code]["current_level_remain"] = float(data["Step2LeftoverQty"])

        self._info[user_code]["year_consume"] = float(data["TotalSq"])

    async def async_get_data(self) -> Payload:
        self._info = {self._user_code: {}}
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.async_get_userinfo(self._user_code))
            tg.create_task(self.async_get_week(self._user_code))
            tg.create_task(self.async_get_year(self._user_code))
            tg.create_task(self.async_get_step(self._user_code))

        _LOGGER.debug("Data %s", self._info)
        return self._info
