
USE WNTRADE;

SELECT FIELD ('JAVA', 'SQL', 'JAVA', 'C');

SELECT FIELD ('오땅', '홈런볼', '오땅', '코콜릿');

SELECT ELT(2, 'SQL', 'JAVA', 'C');

SELECT REPEAT ('*', 5);

SELECT REPLACE('010.1234.5678', '.', '-');

SELECT REVERSE ('OLLEH');

SELECT CEILING(123.56)
, FLOOR (123.56)
, ROUND (123.56)
, ROUND (123.56, 1)
, TRUNCATE(123.56, 1);

SELECT NOW()
	,SYSDATE()
    ,CURDATE()
    ,CURTIME();
    
SELECT NOW() AS 'START', SLEEP(5), NOW() AS 'END';
SELECT SYSDATE() AS 'START', SLEEP(5), SYSDATE() AS 'END';

SELECT CAST('1' AS UNSIGNED)
	,CAST(2 AS CHAR(1))
    ,CONVERT('1', UNSIGNED)
    ,CONVERT(2, CHAR(1));
    
SELECT IF(12500*450>5000000, '초과달성', '미달성');

SELECT *
FROM 고객;

SELECT 고객번호
, IF(마일리지>1000, 'VIP', 'GOLD') AS 등급
FROM 고객;

SELECT 고객번호, 고객회사명, 담당자명
	,IF(마일리지>1000, 'VIP', 'GOLD') AS 등급
FROM 고객;

SELECT CASE WHEN 12500*450>5000000 THEN '초과달성'
	WHEN 2500*450>4000000 THEN '달성'
	ELSE '미달성'
END;

SELECT 주문번호
	, 단가
    , 주문수량
    , 단가*주문수량 AS 주문금액
    , CASE
		WHEN 단가*주문수량 >=5000000 THEN '초과달성'
        WHEN 단가*주문수량 >=4000000 THEN '달성'
        ELSE '미달성'
END AS 달성여부
FROM 주문세부;

SELECT *
FROM 마일리지등급;

SELECT *
FROM 고객;

SELECT 고객번호
, 고객회사명
, 담당자명
, CASE
	WHEN 마일리지 > 10000 THEN 'VIP'
    WHEN 마일리지 BETWEEN 5000 AND 9999 THEN 'GOLD'
    WHEN 마일리지 BETWEEN 3000 AND 49999 THEN 'SILVER'
    ELSE 'BRONZE'
END AS 등급
FROM 고객;

SELECT 사원번호
	, 이름
    , 직위
    , 입사일
    , CASE
		WHEN 부서번호 = 'A1' THEN '영업부'
        WHEN 부서번호 = 'A2' THEN '기획부'
        WHEN 부서번호 = 'A3' THEN '개발부'
        ELSE '기타'
	END AS 부서명
FROM 사원;

SELECT 주문번호
	, 고객번호
    , 사원번호
    , 주문일 
    , 발송일

    , CASE
		WHEN 발송일 IS NULL THEN '배송대기'
        WHEN DATEDIFF(발송일, 주문일) <=4 THEN '빠른배송'
        ELSE '일반배송'
	END AS 배송결과
FROM 주문;

SELECT 도시 
	, COUNT(고객번호)
    , COUNT(도시)
    , COUNT(DISTINCT 지역)
    , SUM(마일리지)
    , AVG(마일리지)
    , MIN(마일리지)
FROM 고객
-- WHERE 도시 LIKE '서울%'
GROUP BY 도시;

SELECT 담당자직위, 도시 
	, COUNT(고객번호)
    , SUM(마일리지)
    , AVG(마일리지)
FROM 고객
GROUP BY 담당자직위, 도시
ORDER BY 1,2;

-- GROUP BY 조건 HAVING
-- 고객, 도시별로 그룹 고객수, 평균 마일리지, 고객수가 >10만 추출
SELECT 도시 
	, COUNT(고객번호)
    , AVG (마일리지)
FROM 고객
GROUP BY 도시
HAVING COUNT(고객번호)>=0;

-- 고객번호 T로 시작하는 고객을 도시별로 묶어 마일리지 합 출력, 단, 1000점 이상
SELECT 도시 
	, SUM(마일리지)
FROM 고객
WHERE 고객번호 LIKE 'T%'
GROUP BY 도시
HAVING SUM(마일리지)>=1000;

-- 광역시 고객, 담당자 직위별로 최대 마일리지, 단, 1만점 이상 레코드만 출력
SELECT 담당자직위 
	, SUM(마일리지)
    , AVG(마일리지)
FROM 고객 
WHERE 도시 LIKE '%광역시'
GROUP BY 담당자직위 
WITH ROLLUP;

-- 크로스 조인
SELECT 부서.부서번호 AS 부서부서번호
	, 사원.부서번호 AS 사원부서번호
    , 이름
    , 부서명 
FROM 부서 JOIN 사원
ON 부서.부서번호=사원.부서번호
WHERE 이름 = '배재용';


SELECT 주문번호, 고객회사명, 주문일, 고객.고객번호
FROM 주문 JOIN 고객
ON 주문.고객번호=고객.고객번호
WHERE 주문.고객번호 = 'ITCWH';

-- 주문, 사원 INNER JOIN  주문번호별 담당자
SELECT 주문번호, 주문.사원번호, 고객번호, 사원.이름
FROM 사원 JOIN 주문
ON 사원.사원번호=주문.사원번호;

-- 고객과 제품의 크로스 조인
SELECT 제품명, 고객회사명
FROM 고객 JOIN 제품;

-- 고객, 마일리지등급
SELECT 고객.고객회사명, 고객.마일리지, 마일리지등급.등급명
FROM 고객 JOIN 마일리지등급
ON 고객.마일리지 BETWEEN 마일리지등급.하한마일리지 AND 마일리지등급.상한마일리지;

SELECT 사원번호
	,직위 
    ,사원.부서번호
    ,부서명 
FROM 사원 JOIN 부서
ON 사원.부서번호=부서.부서번호;

SELECT *
FROM 사원;

SELECT 고객.고객번호, 담당자명, 고객.고객회사명
    , COUNT(주문.주문번호) AS 주문건수
FROM 고객 JOIN 주문
ON 고객.고객번호=주문.고객번호
GROUP BY 고객.고객번호, 고객.고객회사명
ORDER BY COUNT(주문.주문번호) DESC;

SELECT 고객.고객번호
	,담당자명 
    ,고객회사명
    ,COUNT(*) AS 주문건수
FROM 고객 JOIN 주문
ON 고객.고객번호=주문.고객번호
GROUP BY 고객.고객번호
	,담당자명
    ,고객회사명
ORDER BY COUNT(*) DESC;

SELECT 주문번호 
, 이름 AS 사원명
, 입사일 
, 주문일
FROM 주문 JOIN 사원
ON 주문.사원번호=사원.사원번호
AND 주문.주문일 >= 사원.입사일;

-- 고객회사들이 주문한 건수 집계> 건수가 많은 순서로 출력
SELECT 고객.고객번호
, 담당자명
, 고객회사명
, COUNT(*) AS 주문건수
FROM 고객 JOIN 주문
ON 고객.고객번호=주문.고객번호
GROUP BY 고객.고객번호, 담당자명, 고객회사명
ORDER BY COUNT(*) DESC;

-- 고객 회사별 주문금액 합, 큰 금액 순으로 ㅊ출력
SELECT 고객회사명
, SUM(주문수량*단가) AS 주문금액
FROM 고객 JOIN 주문
ON 고객.고객번호=주문.고객번호
JOIN 주문세부 ON 주문.주문번호=주문세부.주문번호
GROUP BY 고객회사명
ORDER BY 2 DESC;

-- 외부조인
SELECT DISTINCT 부서번호
FROM 사원;

SELECT COUNT(*)
FROM 부서;

SELECT 사원번호, 이름, 부서명
FROM 사원 JOIN 부서
ON 사원.부서번호=부서.부서번호;
-- 사원이 없는 부서

SELECT *
FROM 부서 JOIN 사원
ON 부서.부서번호=사원.부서번호
GRUOP BY 부서.부서번호;



