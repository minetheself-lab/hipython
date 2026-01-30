USE WNTRADE;
SELECT * FROM wntrade.사원;
select 이름 as 직원명, 주소, 직위 from 사원;

select 제품명
	, 재고 as 구매가능수량
	, 단가 
from 제품;
select 제품명
, FORMAT(단가, 0) AS 단가
, 재고 AS "구매 가능 수량!!"
, FORMAT(단가*재고, 0) AS "주문가능금액"
FROM 제품;

#주문내역정보 출력- 제품번호, 단가, 주문수량, 할인율, 주문금액
SELECT 제품번호
, FORMAT(단가, 0) AS 단가
, 주문수량
, 할인율
, FORMAT (단가*주문수량, 0) AS 주문금액
, FORMAT (단가*주문수량*할인율, 0) AS 할인금액
FROM 주문세부
ORDER BY 6 DESC;

SELECT 고객번호
, 담당자명
, 고객회사명
, 마일리지 AS 포인트
, 마일리지*1.1 AS "10%인상된 마일리지"
FROM 고객;

SELECT 고객번호
, 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 >=100000;

SELECT 제품명
, 재고
, 단가
FROM 제품
WHERE 단가*재고 >100000;

SELECT 제품번호
, FORMAT(단가, 0) AS 단가
, 주문수량
, 할인율
, FORMAT (단가*주문수량, 0) AS 주문금액
, FORMAT (단가*주문수량*할인율, 0) AS 할인금액
FROM 주문세부
ORDER BY 단가*주문수량*할인율 DESC;
-- LIMIT 10;

SELECT *
FROM 고객
LIMIT 5;

SELECT *
FROM 고객
ORDER BY 9 DESC
LIMIT 3;

SELECT *
FROM 고객
WHERE 도시 ='서울특별시'
ORDER BY 5 DESC
LIMIT 10;

SELECT *
FROM 마일리지등급
WHERE 등급명='A'
ORDER BY 1 ASC;

SELECT *
FROM 부서
ORDER BY 2 DESC;

SELECT *
FROM 사원
WHERE 도시= '서울특별시'
ORDER BY 7 DESC;

SELECT 이름
FROM 사원
WHERE 이름 LIKE '%소%';

SELECT *
FROM 제품
WHERE 제품명 LIKE '썬%'
ORDER BY 4 DESC
LIMIT 2;

SELECT *
FROM 주문
ORDER BY 5 DESC
LIMIT 20;

SELECT *
, 단가*주문수량 AS 주문금액
FROM 주문세부
ORDER BY 6 DESC
LIMIT 20;

SELECT distinct 도시
FROM 고객;


SELECT 23+5 AS 더하기
, 23-5 AS 빼기
, 23*5 AS 곱하기
, 23/5 AS 실수나누기
, 23 DIV 5 AS 정수나누기
, 23 % 5 AS 나머지1
, 23 MOD 5 AS 나머지2;

SELECT '오늘 고개은',current_date, 담당자명
FROM 고객;

SELECT 23>=5
, 23<=5
, 23> 23
, 23<23
, 23=23
, 23!=23
, 23<>23;

SELECT *
FROM 고객
WHERE 담당자직위 <> '대표이사';

SELECT *
FROM 주문
WHERE 주문일 <2021-01-01;

DESCRIBE 주문;

SELECT *
FROM 고객
WHERE 도시 = '부산광역시'
AND 마일리지 < 1000;

SELECT *
FROM 고객
WHERE 도시= '서울특별시'
AND 마일리지 > 5000
ORDER BY 9 DESC;

SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
OR 마일리지 > 10000
ORDER BY 9 DESC;

SELECT *
FROM 고객
WHERE 도시 <>'서울특별시';

SELECT *
FROM 고객
WHERE 도시 <>'서울특별시'
AND 마일리지>5000;

SELECT *
FROM 고객
WHERE 도시 ='서울특별시'
OR 도시='부산광역시';

SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 도시= '부산광역시'
UNION
SELECT 고객번호
, 담당자명
, 마일리지
, 도시
FROM 고객
WHERE 마일리지 <1000
ORDER BY 1;

SELECT *
FROM 주문세부
WHERE 단가 >= 5000
UNION
SELECT *
FROM 주문세부
WHERE 할인율 >=0.5;

SELECT 도시
FROM 고객
UNION ALL
SELECT 도시
FROM 사원;

SELECT *
FROM 고객
WHERE 지역 IS NULL;

SELECT DISTINCT *
FROM 고객
ORDER BY 지역=''DESC, 도시;

SELECT 고객번호
, 담당자명
, 담당자직위
FROM 고객
WHERE 담당자직위 IN ('영업 과장', '마케팅 과장');

SELECT 담당자명
, 마일리지
FROM 고객
WHERE 마일리지 BETWEEN 100000 AND 200000;

SELECT *
FROM 사원
WHERE 부서번호 IN('A1', 'A2');

SELECT *
FROM 고객 WHERE 담당자명 BETWEEN '권기호' AND '김도현'
ORDER BY 담당자명 ASC;

select 고객번호
FROM 고객
WHERE 고객번호 LIKE '%C';

SELECT *
FROM 고객
WHERE (도시 LIKE '%광역시')
AND (고객번호 LIKE '_C%' OR 고객번호 LIKE '_C%' OR 고객번호 LIKE '__C%');


