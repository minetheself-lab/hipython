use wntrade;
show tables;
select*from wntrade.고객;

select 사원번호, 이름, 부서명
from 사원 left join 부서
on 사원.부서번호 = 부서.부서번호;

use wntrade;
SELECT  A.고객회사명, A.담당자명, A.마일리지
FROM 고객 A
LEFT JOIN 고객 B
ON A.마일리지 < B.마일리지
WHERE B.고객번호 IS NULL;

select 사원번호, 이름, 부서명
from 사원 left join 부서
on 사원.부서번호 = 부서.부서번호;

select 고객번호
	, 고객회사명
    , 담당자명 
    , 마일리지
    , 등급명 
from 고객
inner join 마일리지등급
on 마일리지 >= 하한마일리지
and 마일리지 <= 상한마일리지 
where 담당자명 = '이은광';


-- 사원이 없는 부서
select 부서명, 사원.*
from 사원 right join 부서
on 사원.부서번호 = 부서.부서번호;

select 이름, 부서.*
from 사원 left outer join 부서
on 사원.부서번호 = 부서.부서번호
where 부서.부서번호 is null;

-- 주문안한 고객
select 고객.고객회사명, 고객.담당자명
from 고객 left join 주문 
on 고객.고객번호=주문.고객번호
where 주문.주문번호 is null;

-- 사원, 상사이름
select 사원.사원번호
	,사원.이름
    ,상사.사원번호 as '상사의 사원번호'
    ,상사.이름 as '상사의 이름'
from 사원
inner join 사원 as 상사
on 사원.상사번호 = 상사.사원번호;

-- 셀프조인, 사원별 상사의 이름
select 사원.이름, 상사.이름
from 사원
left join 사원 as 상사
on 사원.상사번호 = 상사.사원번호
where 사원.상사번호 = '';

select 고객번호
	,고객회사명
    ,담당자명
    ,마일리지
from 고객
where 마일리지= (select max(마일리지)
				from 고객
                );

select a.고객회사명, a.담당자명, a.마일리지
from 고객 as a
left join 고객 as b
on a.마일리지 <b.마일리지
order by a.마일리지 desc;


-- 조인 사용 주문번호 HO250 추출
select 고객.고객회사명
	,고객.담당자명
from 고객
inner join 주문 
on 고객.고객번호=주문.고객번호
where 주문번호= 'H0250';

-- 서브쿼리버전 
SELECT 고객.고객회사명, 고객.담당자명
FROM 고객
WHERE 고객.고객번호=(
		SELECT 주문.고객번호
        FROM 주문
        WHERE 주문.주문번호='H0250'
);

SELECT 고객.고객회사명, 고객.담당자명, 마일리지
FROM 고객
WHERE 고객.마일리지 > (
		SELECT MIN(마일리지)
        FROM 고객
        WHERE 고객.도시='부산광역시'
	);

SELECT COUNT(*) AS 주문건수
FROM 주문 
WHERE 고객번호 IN (SELECT 고객번호
				FROM 고객
                WHERE 도시 = '부산광역시'
                );


select 고객회사명, 담당자명, 마일리지
from 고객
where 마일리지 > any ( select 마일리지
					from 고객 
                    where 도시 ='부산광역시'
                    );




select 고객회사명, 담당자명, 마일리지
from 고객
where 마일리지 > all ( select 마일리지
					from 고객 
                    where 도시 ='부산광역시'
                    );

select 담당자명, 고객회사명, 마일리지
from 고객 as a
where exists (
	select 1
    from 고객 b
    where 도시 = '부산광역시' and a.마일리지> b.마일리지
);

select 도시, avg(마일리지) as 평균마일리지, (select avg(마일리지)
					from 고객
					) as 전체평균마일리지
from 고객 
group by 도시
having avg(마일리지) > (select avg(마일리지)
					from 고객
					);
                    
SELECT 고객번호
	,담당자명
    ,마일리지
    ,등급.*
FROM 고객
CROSS JOIN 마일리지등급 AS 등급
WHERE 담당자명 = '이은광';

select 사원번호
	,이름
    ,부서명
from 사원
left outer join 부서 
on 사원.부서번호 = 부서.부서번호
where 성별='여';

select 부서명
	,사원.*
from 사원 
right outer join 부서
on 사원.부서번호=부서.부서번호
where 사원.부서번호 is null;

select 사원.이름 as 이름 
	,사원.직위
    ,상사.이름 as 상사이름
from 사원 as 상사
right outer join 사원
on 사원.상사번호=상사.사원번호
order by 상사이름;

select 사원.이름 as 이름
	,사원.직위
    ,상사.이름 as 상사이름
from 사원 
left outer join 사원 as 상사
on 사원.상사번호=상사.사원번호
order by 상사이름;

select 고객번호
	,고객회사명
    ,담당자명
    ,마일리지
from 고객
where 마일리지=(select max(마일리지)
			from 고객
            );

select 고객번호
	,고객회사명
    ,담당자명
    ,마일리지 
from 고객
where 마일리지=(select max(마일리지)
				from 고객);

select 고객번호, 고객회사명, 도시, 마일리지
from 고객
where 마일리지>(select min(마일리지)
				from 고객 
                where 도시='부산광역시');

select count(*) as 주문건수
from 주문 
where 고객번호 in (select 고객번호
				from 고객
                where 도시= '부산광역시'
                );

select 고객번호, 고객회사명, 도시, 마일리지
from 고객
where 마일리지 > any (select 마일리지
				from 고객
                where 도시='부산광역시' 
                );

select 고객번호, 고객회사명, 도시, 마일리지
from 고객 
where 마일리지 > all(select avg(마일리지)
					from 고객
                    group by 도시
                    );





