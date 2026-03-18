var qd=Object.defineProperty;var di=e=>{throw TypeError(e)};var Fd=(e,t,r)=>t in e?qd(e,t,{enumerable:!0,configurable:!0,writable:!0,value:r}):e[t]=r;var dn=(e,t,r)=>Fd(e,typeof t!="symbol"?t+"":t,r),no=(e,t,r)=>t.has(e)||di("Cannot "+r);var M=(e,t,r)=>(no(e,t,"read from private field"),r?r.call(e):t.get(e)),et=(e,t,r)=>t.has(e)?di("Cannot add the same private member more than once"):t instanceof WeakSet?t.add(e):t.set(e,r),Ge=(e,t,r,a)=>(no(e,t,"write to private field"),a?a.call(e,r):t.set(e,r),r),nr=(e,t,r)=>(no(e,t,"access private method"),r);(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))a(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const i of o.addedNodes)i.tagName==="LINK"&&i.rel==="modulepreload"&&a(i)}).observe(document,{childList:!0,subtree:!0});function r(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function a(s){if(s.ep)return;s.ep=!0;const o=r(s);fetch(s.href,o)}})();const fo=!1;var Oo=Array.isArray,Bd=Array.prototype.indexOf,Ya=Array.prototype.includes,Us=Array.from,Gd=Object.defineProperty,ia=Object.getOwnPropertyDescriptor,Gi=Object.getOwnPropertyDescriptors,Hd=Object.prototype,Ud=Array.prototype,Ro=Object.getPrototypeOf,ci=Object.isExtensible;function ls(e){return typeof e=="function"}const Wd=()=>{};function Kd(e){return e()}function vo(e){for(var t=0;t<e.length;t++)e[t]()}function Hi(){var e,t,r=new Promise((a,s)=>{e=a,t=s});return{promise:r,resolve:e,reject:t}}function Ui(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const r=[];for(const a of e)if(r.push(a),r.length===t)break;return r}const _r=2,ts=4,za=8,Ws=1<<24,va=16,hn=32,Na=64,po=128,Qr=512,gr=1024,xr=2048,mn=4096,zr=8192,En=16384,rs=32768,Fn=65536,ui=1<<17,Yd=1<<18,ns=1<<19,Wi=1<<20,Sn=1<<25,Ta=65536,mo=1<<21,Do=1<<22,la=1<<23,An=Symbol("$state"),Ki=Symbol("legacy props"),Xd=Symbol(""),xa=new class extends Error{constructor(){super(...arguments);dn(this,"name","StaleReactionError");dn(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}};var qi;const Yi=!!((qi=globalThis.document)!=null&&qi.contentType)&&globalThis.document.contentType.includes("xml");function Jd(){throw new Error("https://svelte.dev/e/async_derived_orphan")}function Qd(e,t,r){throw new Error("https://svelte.dev/e/each_key_duplicate")}function Zd(e){throw new Error("https://svelte.dev/e/effect_in_teardown")}function ec(){throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function tc(e){throw new Error("https://svelte.dev/e/effect_orphan")}function rc(){throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function nc(e){throw new Error("https://svelte.dev/e/props_invalid_value")}function ac(){throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function sc(){throw new Error("https://svelte.dev/e/state_prototype_fixed")}function oc(){throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ic(){throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const lc=1,dc=2,Xi=4,cc=8,uc=16,fc=1,vc=2,Ji=4,pc=8,mc=16,hc=1,gc=2,cr=Symbol(),Qi="http://www.w3.org/1999/xhtml",Zi="http://www.w3.org/2000/svg",xc="http://www.w3.org/1998/Math/MathML",bc="@attach";function _c(){console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function wc(){console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function el(e){return e===this.v}function yc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function tl(e){return!yc(e,this.v)}let Ms=!1,kc=!1;function Cc(){Ms=!0}let ur=null;function Xa(e){ur=e}function rn(e,t=!1,r){ur={p:ur,i:!1,c:null,e:null,s:e,x:null,l:Ms&&!t?{s:null,u:null,$:[]}:null}}function nn(e){var t=ur,r=t.e;if(r!==null){t.e=null;for(var a of r)_l(a)}return t.i=!0,ur=t.p,{}}function Es(){return!Ms||ur!==null&&ur.l===null}let ba=[];function rl(){var e=ba;ba=[],vo(e)}function zn(e){if(ba.length===0&&!gs){var t=ba;queueMicrotask(()=>{t===ba&&rl()})}ba.push(e)}function Sc(){for(;ba.length>0;)rl()}function nl(e){var t=Ze;if(t===null)return Qe.f|=la,e;if((t.f&rs)===0&&(t.f&ts)===0)throw e;sa(e,t)}function sa(e,t){for(;t!==null;){if((t.f&po)!==0){if((t.f&rs)===0)throw e;try{t.b.error(e);return}catch(r){e=r}}t=t.parent}throw e}const Mc=-7169;function Kt(e,t){e.f=e.f&Mc|t}function jo(e){(e.f&Qr)!==0||e.deps===null?Kt(e,gr):Kt(e,mn)}function al(e){if(e!==null)for(const t of e)(t.f&_r)===0||(t.f&Ta)===0||(t.f^=Ta,al(t.deps))}function sl(e,t,r){(e.f&xr)!==0?t.add(e):(e.f&mn)!==0&&r.add(e),al(e.deps),Kt(e,gr)}const Ns=new Set;let He=null,ho=null,hr=null,$r=[],Ks=null,gs=!1,Ja=null,Ec=1;var ra,qa,ya,Fa,Ba,Ga,na,wn,Ha,Rr,go,xo,bo,_o;const Jo=class Jo{constructor(){et(this,Rr);dn(this,"id",Ec++);dn(this,"current",new Map);dn(this,"previous",new Map);et(this,ra,new Set);et(this,qa,new Set);et(this,ya,0);et(this,Fa,0);et(this,Ba,null);et(this,Ga,new Set);et(this,na,new Set);et(this,wn,new Map);dn(this,"is_fork",!1);et(this,Ha,!1)}skip_effect(t){M(this,wn).has(t)||M(this,wn).set(t,{d:[],m:[]})}unskip_effect(t){var r=M(this,wn).get(t);if(r){M(this,wn).delete(t);for(var a of r.d)Kt(a,xr),Mn(a);for(a of r.m)Kt(a,mn),Mn(a)}}process(t){var s;$r=[],this.apply();var r=Ja=[],a=[];for(const o of t)nr(this,Rr,xo).call(this,o,r,a);if(Ja=null,nr(this,Rr,go).call(this)){nr(this,Rr,bo).call(this,a),nr(this,Rr,bo).call(this,r);for(const[o,i]of M(this,wn))dl(o,i)}else{ho=this,He=null;for(const o of M(this,ra))o(this);M(this,ra).clear(),M(this,ya)===0&&nr(this,Rr,_o).call(this),fi(a),fi(r),M(this,Ga).clear(),M(this,na).clear(),ho=null,(s=M(this,Ba))==null||s.resolve()}hr=null}capture(t,r){r!==cr&&!this.previous.has(t)&&this.previous.set(t,r),(t.f&la)===0&&(this.current.set(t,t.v),hr==null||hr.set(t,t.v))}activate(){He=this,this.apply()}deactivate(){He===this&&(He=null,hr=null)}flush(){var t;if($r.length>0)He=this,ol();else if(M(this,ya)===0&&!this.is_fork){for(const r of M(this,ra))r(this);M(this,ra).clear(),nr(this,Rr,_o).call(this),(t=M(this,Ba))==null||t.resolve()}this.deactivate()}discard(){for(const t of M(this,qa))t(this);M(this,qa).clear()}increment(t){Ge(this,ya,M(this,ya)+1),t&&Ge(this,Fa,M(this,Fa)+1)}decrement(t){Ge(this,ya,M(this,ya)-1),t&&Ge(this,Fa,M(this,Fa)-1),!M(this,Ha)&&(Ge(this,Ha,!0),zn(()=>{Ge(this,Ha,!1),nr(this,Rr,go).call(this)?$r.length>0&&this.flush():this.revive()}))}revive(){for(const t of M(this,Ga))M(this,na).delete(t),Kt(t,xr),Mn(t);for(const t of M(this,na))Kt(t,mn),Mn(t);this.flush()}oncommit(t){M(this,ra).add(t)}ondiscard(t){M(this,qa).add(t)}settled(){return(M(this,Ba)??Ge(this,Ba,Hi())).promise}static ensure(){if(He===null){const t=He=new Jo;Ns.add(He),gs||zn(()=>{He===t&&t.flush()})}return He}apply(){}};ra=new WeakMap,qa=new WeakMap,ya=new WeakMap,Fa=new WeakMap,Ba=new WeakMap,Ga=new WeakMap,na=new WeakMap,wn=new WeakMap,Ha=new WeakMap,Rr=new WeakSet,go=function(){return this.is_fork||M(this,Fa)>0},xo=function(t,r,a){t.f^=gr;for(var s=t.first;s!==null;){var o=s.f,i=(o&(hn|Na))!==0,l=i&&(o&gr)!==0,c=(o&zr)!==0,f=l||M(this,wn).has(s);if(!f&&s.fn!==null){i?c||(s.f^=gr):(o&ts)!==0?r.push(s):(o&(za|Ws))!==0&&c?a.push(s):Ts(s)&&(Za(s),(o&va)!==0&&(M(this,na).add(s),c&&Kt(s,xr)));var p=s.first;if(p!==null){s=p;continue}}for(;s!==null;){var b=s.next;if(b!==null){s=b;break}s=s.parent}}},bo=function(t){for(var r=0;r<t.length;r+=1)sl(t[r],M(this,Ga),M(this,na))},_o=function(){var o;if(Ns.size>1){this.previous.clear();var t=He,r=hr,a=!0;for(const i of Ns){if(i===this){a=!1;continue}const l=[];for(const[f,p]of this.current){if(i.current.has(f))if(a&&p!==i.current.get(f))i.current.set(f,p);else continue;l.push(f)}if(l.length===0)continue;const c=[...i.current.keys()].filter(f=>!this.current.has(f));if(c.length>0){var s=$r;$r=[];const f=new Set,p=new Map;for(const b of l)il(b,c,f,p);if($r.length>0){He=i,i.apply();for(const b of $r)nr(o=i,Rr,xo).call(o,b,[],[]);i.deactivate()}$r=s}}He=t,hr=r}M(this,wn).clear(),Ns.delete(this)};let da=Jo;function Ac(e){var t=gs;gs=!0;try{for(var r;;){if(Sc(),$r.length===0&&(He==null||He.flush(),$r.length===0))return Ks=null,r;ol()}}finally{gs=t}}function ol(){var e=null;try{for(var t=0;$r.length>0;){var r=da.ensure();if(t++>1e3){var a,s;zc()}r.process($r),ca.clear()}}finally{$r=[],Ks=null,Ja=null}}function zc(){try{rc()}catch(e){sa(e,Ks)}}let cn=null;function fi(e){var t=e.length;if(t!==0){for(var r=0;r<t;){var a=e[r++];if((a.f&(En|zr))===0&&Ts(a)&&(cn=new Set,Za(a),a.deps===null&&a.first===null&&a.nodes===null&&a.teardown===null&&a.ac===null&&Cl(a),(cn==null?void 0:cn.size)>0)){ca.clear();for(const s of cn){if((s.f&(En|zr))!==0)continue;const o=[s];let i=s.parent;for(;i!==null;)cn.has(i)&&(cn.delete(i),o.push(i)),i=i.parent;for(let l=o.length-1;l>=0;l--){const c=o[l];(c.f&(En|zr))===0&&Za(c)}}cn.clear()}}cn=null}}function il(e,t,r,a){if(!r.has(e)&&(r.add(e),e.reactions!==null))for(const s of e.reactions){const o=s.f;(o&_r)!==0?il(s,t,r,a):(o&(Do|va))!==0&&(o&xr)===0&&ll(s,t,a)&&(Kt(s,xr),Mn(s))}}function ll(e,t,r){const a=r.get(e);if(a!==void 0)return a;if(e.deps!==null)for(const s of e.deps){if(Ya.call(t,s))return!0;if((s.f&_r)!==0&&ll(s,t,r))return r.set(s,!0),!0}return r.set(e,!1),!1}function Mn(e){var t=Ks=e,r=t.b;if(r!=null&&r.is_pending&&(e.f&(ts|za|Ws))!==0&&(e.f&rs)===0){r.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var a=t.f;if(Ja!==null&&t===Ze&&(e.f&za)===0)return;if((a&(Na|hn))!==0){if((a&gr)===0)return;t.f^=gr}}$r.push(t)}function dl(e,t){if(!((e.f&hn)!==0&&(e.f&gr)!==0)){(e.f&xr)!==0?t.d.push(e):(e.f&mn)!==0&&t.m.push(e),Kt(e,gr);for(var r=e.first;r!==null;)dl(r,t),r=r.next}}function Tc(e){let t=0,r=ua(0),a;return()=>{Bo()&&(n(r),Ho(()=>(t===0&&(a=Ia(()=>e(()=>bs(r)))),t+=1,()=>{zn(()=>{t-=1,t===0&&(a==null||a(),a=void 0,bs(r))})})))}}var Ic=Fn|ns;function Pc(e,t,r,a){new Nc(e,t,r,a)}var Jr,Lo,yn,ka,Nr,kn,Gr,un,On,Ca,aa,Ua,Wa,Ka,Rn,Gs,sr,$c,Lc,Oc,wo,Ds,js,yo;class Nc{constructor(t,r,a,s){et(this,sr);dn(this,"parent");dn(this,"is_pending",!1);dn(this,"transform_error");et(this,Jr);et(this,Lo,null);et(this,yn);et(this,ka);et(this,Nr);et(this,kn,null);et(this,Gr,null);et(this,un,null);et(this,On,null);et(this,Ca,0);et(this,aa,0);et(this,Ua,!1);et(this,Wa,new Set);et(this,Ka,new Set);et(this,Rn,null);et(this,Gs,Tc(()=>(Ge(this,Rn,ua(M(this,Ca))),()=>{Ge(this,Rn,null)})));var o;Ge(this,Jr,t),Ge(this,yn,r),Ge(this,ka,i=>{var l=Ze;l.b=this,l.f|=po,a(i)}),this.parent=Ze.b,this.transform_error=s??((o=this.parent)==null?void 0:o.transform_error)??(i=>i),Ge(this,Nr,as(()=>{nr(this,sr,wo).call(this)},Ic))}defer_effect(t){sl(t,M(this,Wa),M(this,Ka))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!M(this,yn).pending}update_pending_count(t){nr(this,sr,yo).call(this,t),Ge(this,Ca,M(this,Ca)+t),!(!M(this,Rn)||M(this,Ua))&&(Ge(this,Ua,!0),zn(()=>{Ge(this,Ua,!1),M(this,Rn)&&Qa(M(this,Rn),M(this,Ca))}))}get_effect_pending(){return M(this,Gs).call(this),n(M(this,Rn))}error(t){var r=M(this,yn).onerror;let a=M(this,yn).failed;if(!r&&!a)throw t;M(this,kn)&&(br(M(this,kn)),Ge(this,kn,null)),M(this,Gr)&&(br(M(this,Gr)),Ge(this,Gr,null)),M(this,un)&&(br(M(this,un)),Ge(this,un,null));var s=!1,o=!1;const i=()=>{if(s){wc();return}s=!0,o&&ic(),M(this,un)!==null&&Ma(M(this,un),()=>{Ge(this,un,null)}),nr(this,sr,js).call(this,()=>{da.ensure(),nr(this,sr,wo).call(this)})},l=c=>{try{o=!0,r==null||r(c,i),o=!1}catch(f){sa(f,M(this,Nr)&&M(this,Nr).parent)}a&&Ge(this,un,nr(this,sr,js).call(this,()=>{da.ensure();try{return Or(()=>{var f=Ze;f.b=this,f.f|=po,a(M(this,Jr),()=>c,()=>i)})}catch(f){return sa(f,M(this,Nr).parent),null}}))};zn(()=>{var c;try{c=this.transform_error(t)}catch(f){sa(f,M(this,Nr)&&M(this,Nr).parent);return}c!==null&&typeof c=="object"&&typeof c.then=="function"?c.then(l,f=>sa(f,M(this,Nr)&&M(this,Nr).parent)):l(c)})}}Jr=new WeakMap,Lo=new WeakMap,yn=new WeakMap,ka=new WeakMap,Nr=new WeakMap,kn=new WeakMap,Gr=new WeakMap,un=new WeakMap,On=new WeakMap,Ca=new WeakMap,aa=new WeakMap,Ua=new WeakMap,Wa=new WeakMap,Ka=new WeakMap,Rn=new WeakMap,Gs=new WeakMap,sr=new WeakSet,$c=function(){try{Ge(this,kn,Or(()=>M(this,ka).call(this,M(this,Jr))))}catch(t){this.error(t)}},Lc=function(t){const r=M(this,yn).failed;r&&Ge(this,un,Or(()=>{r(M(this,Jr),()=>t,()=>()=>{})}))},Oc=function(){const t=M(this,yn).pending;t&&(this.is_pending=!0,Ge(this,Gr,Or(()=>t(M(this,Jr)))),zn(()=>{var r=Ge(this,On,document.createDocumentFragment()),a=Tn();r.append(a),Ge(this,kn,nr(this,sr,js).call(this,()=>(da.ensure(),Or(()=>M(this,ka).call(this,a))))),M(this,aa)===0&&(M(this,Jr).before(r),Ge(this,On,null),Ma(M(this,Gr),()=>{Ge(this,Gr,null)}),nr(this,sr,Ds).call(this))}))},wo=function(){try{if(this.is_pending=this.has_pending_snippet(),Ge(this,aa,0),Ge(this,Ca,0),Ge(this,kn,Or(()=>{M(this,ka).call(this,M(this,Jr))})),M(this,aa)>0){var t=Ge(this,On,document.createDocumentFragment());Ko(M(this,kn),t);const r=M(this,yn).pending;Ge(this,Gr,Or(()=>r(M(this,Jr))))}else nr(this,sr,Ds).call(this)}catch(r){this.error(r)}},Ds=function(){this.is_pending=!1;for(const t of M(this,Wa))Kt(t,xr),Mn(t);for(const t of M(this,Ka))Kt(t,mn),Mn(t);M(this,Wa).clear(),M(this,Ka).clear()},js=function(t){var r=Ze,a=Qe,s=ur;tn(M(this,Nr)),en(M(this,Nr)),Xa(M(this,Nr).ctx);try{return t()}catch(o){return nl(o),null}finally{tn(r),en(a),Xa(s)}},yo=function(t){var r;if(!this.has_pending_snippet()){this.parent&&nr(r=this.parent,sr,yo).call(r,t);return}Ge(this,aa,M(this,aa)+t),M(this,aa)===0&&(nr(this,sr,Ds).call(this),M(this,Gr)&&Ma(M(this,Gr),()=>{Ge(this,Gr,null)}),M(this,On)&&(M(this,Jr).before(M(this,On)),Ge(this,On,null)))};function cl(e,t,r,a){const s=Es()?As:Vo;var o=e.filter(b=>!b.settled);if(r.length===0&&o.length===0){a(t.map(s));return}var i=Ze,l=Rc(),c=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(b=>b.promise)):null;function f(b){l();try{a(b)}catch(_){(i.f&En)===0&&sa(_,i)}ko()}if(r.length===0){c.then(()=>f(t.map(s)));return}function p(){l(),Promise.all(r.map(b=>jc(b))).then(b=>f([...t.map(s),...b])).catch(b=>sa(b,i))}c?c.then(p):p()}function Rc(){var e=Ze,t=Qe,r=ur,a=He;return function(o=!0){tn(e),en(t),Xa(r),o&&(a==null||a.activate())}}function ko(e=!0){tn(null),en(null),Xa(null),e&&(He==null||He.deactivate())}function Dc(){var e=Ze.b,t=He,r=e.is_rendered();return e.update_pending_count(1),t.increment(r),()=>{e.update_pending_count(-1),t.decrement(r)}}function As(e){var t=_r|xr,r=Qe!==null&&(Qe.f&_r)!==0?Qe:null;return Ze!==null&&(Ze.f|=ns),{ctx:ur,deps:null,effects:null,equals:el,f:t,fn:e,reactions:null,rv:0,v:cr,wv:0,parent:r??Ze,ac:null}}function jc(e,t,r){Ze===null&&Jd();var s=void 0,o=ua(cr),i=!Qe,l=new Map;return eu(()=>{var _;var c=Hi();s=c.promise;try{Promise.resolve(e()).then(c.resolve,c.reject).finally(ko)}catch(z){c.reject(z),ko()}var f=He;if(i){var p=Dc();(_=l.get(f))==null||_.reject(xa),l.delete(f),l.set(f,c)}const b=(z,y=void 0)=>{if(f.activate(),y)y!==xa&&(o.f|=la,Qa(o,y));else{(o.f&la)!==0&&(o.f^=la),Qa(o,z);for(const[I,k]of l){if(l.delete(I),I===f)break;k.reject(xa)}}p&&p()};c.promise.then(b,z=>b(null,z||"unknown"))}),Xs(()=>{for(const c of l.values())c.reject(xa)}),new Promise(c=>{function f(p){function b(){p===s?c(o):f(s)}p.then(b,b)}f(s)})}function B(e){const t=As(e);return El(t),t}function Vo(e){const t=As(e);return t.equals=tl,t}function Vc(e){var t=e.effects;if(t!==null){e.effects=null;for(var r=0;r<t.length;r+=1)br(t[r])}}function qc(e){for(var t=e.parent;t!==null;){if((t.f&_r)===0)return(t.f&En)===0?t:null;t=t.parent}return null}function qo(e){var t,r=Ze;tn(qc(e));try{e.f&=~Ta,Vc(e),t=Il(e)}finally{tn(r)}return t}function ul(e){var t=qo(e);if(!e.equals(t)&&(e.wv=zl(),(!(He!=null&&He.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Kt(e,gr);return}fa||(hr!==null?(Bo()||He!=null&&He.is_fork)&&hr.set(e,t):jo(e))}function Fc(e){var t,r;if(e.effects!==null)for(const a of e.effects)(a.teardown||a.ac)&&((t=a.teardown)==null||t.call(a),(r=a.ac)==null||r.abort(xa),a.teardown=Wd,a.ac=null,ks(a,0),Uo(a))}function fl(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Za(t)}let Co=new Set;const ca=new Map;let vl=!1;function ua(e,t){var r={f:0,v:e,reactions:null,equals:el,rv:0,wv:0};return r}function G(e,t){const r=ua(e);return El(r),r}function Bc(e,t=!1,r=!0){var s;const a=ua(e);return t||(a.equals=tl),Ms&&r&&ur!==null&&ur.l!==null&&((s=ur.l).s??(s.s=[])).push(a),a}function u(e,t,r=!1){Qe!==null&&(!pn||(Qe.f&ui)!==0)&&Es()&&(Qe.f&(_r|va|Do|ui))!==0&&(Zr===null||!Ya.call(Zr,e))&&oc();let a=r?qt(t):t;return Qa(e,a)}function Qa(e,t){if(!e.equals(t)){var r=e.v;fa?ca.set(e,t):ca.set(e,r),e.v=t;var a=da.ensure();if(a.capture(e,r),(e.f&_r)!==0){const s=e;(e.f&xr)!==0&&qo(s),jo(s)}e.wv=zl(),pl(e,xr),Es()&&Ze!==null&&(Ze.f&gr)!==0&&(Ze.f&(hn|Na))===0&&(Xr===null?ru([e]):Xr.push(e)),!a.is_fork&&Co.size>0&&!vl&&Gc()}return t}function Gc(){vl=!1;for(const e of Co)(e.f&gr)!==0&&Kt(e,mn),Ts(e)&&Za(e);Co.clear()}function xs(e,t=1){var r=n(e),a=t===1?r++:r--;return u(e,r),a}function bs(e){u(e,e.v+1)}function pl(e,t){var r=e.reactions;if(r!==null)for(var a=Es(),s=r.length,o=0;o<s;o++){var i=r[o],l=i.f;if(!(!a&&i===Ze)){var c=(l&xr)===0;if(c&&Kt(i,t),(l&_r)!==0){var f=i;hr==null||hr.delete(f),(l&Ta)===0&&(l&Qr&&(i.f|=Ta),pl(f,mn))}else c&&((l&va)!==0&&cn!==null&&cn.add(i),Mn(i))}}}function qt(e){if(typeof e!="object"||e===null||An in e)return e;const t=Ro(e);if(t!==Hd&&t!==Ud)return e;var r=new Map,a=Oo(e),s=G(0),o=Ea,i=l=>{if(Ea===o)return l();var c=Qe,f=Ea;en(null),hi(o);var p=l();return en(c),hi(f),p};return a&&r.set("length",G(e.length)),new Proxy(e,{defineProperty(l,c,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&ac();var p=r.get(c);return p===void 0?i(()=>{var b=G(f.value);return r.set(c,b),b}):u(p,f.value,!0),!0},deleteProperty(l,c){var f=r.get(c);if(f===void 0){if(c in l){const p=i(()=>G(cr));r.set(c,p),bs(s)}}else u(f,cr),bs(s);return!0},get(l,c,f){var z;if(c===An)return e;var p=r.get(c),b=c in l;if(p===void 0&&(!b||(z=ia(l,c))!=null&&z.writable)&&(p=i(()=>{var y=qt(b?l[c]:cr),I=G(y);return I}),r.set(c,p)),p!==void 0){var _=n(p);return _===cr?void 0:_}return Reflect.get(l,c,f)},getOwnPropertyDescriptor(l,c){var f=Reflect.getOwnPropertyDescriptor(l,c);if(f&&"value"in f){var p=r.get(c);p&&(f.value=n(p))}else if(f===void 0){var b=r.get(c),_=b==null?void 0:b.v;if(b!==void 0&&_!==cr)return{enumerable:!0,configurable:!0,value:_,writable:!0}}return f},has(l,c){var _;if(c===An)return!0;var f=r.get(c),p=f!==void 0&&f.v!==cr||Reflect.has(l,c);if(f!==void 0||Ze!==null&&(!p||(_=ia(l,c))!=null&&_.writable)){f===void 0&&(f=i(()=>{var z=p?qt(l[c]):cr,y=G(z);return y}),r.set(c,f));var b=n(f);if(b===cr)return!1}return p},set(l,c,f,p){var U;var b=r.get(c),_=c in l;if(a&&c==="length")for(var z=f;z<b.v;z+=1){var y=r.get(z+"");y!==void 0?u(y,cr):z in l&&(y=i(()=>G(cr)),r.set(z+"",y))}if(b===void 0)(!_||(U=ia(l,c))!=null&&U.writable)&&(b=i(()=>G(void 0)),u(b,qt(f)),r.set(c,b));else{_=b.v!==cr;var I=i(()=>qt(f));u(b,I)}var k=Reflect.getOwnPropertyDescriptor(l,c);if(k!=null&&k.set&&k.set.call(p,f),!_){if(a&&typeof c=="string"){var C=r.get("length"),L=Number(c);Number.isInteger(L)&&L>=C.v&&u(C,L+1)}bs(s)}return!0},ownKeys(l){n(s);var c=Reflect.ownKeys(l).filter(b=>{var _=r.get(b);return _===void 0||_.v!==cr});for(var[f,p]of r)p.v!==cr&&!(f in l)&&c.push(f);return c},setPrototypeOf(){sc()}})}function vi(e){try{if(e!==null&&typeof e=="object"&&An in e)return e[An]}catch{}return e}function Hc(e,t){return Object.is(vi(e),vi(t))}var So,ml,hl,gl;function Uc(){if(So===void 0){So=window,ml=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,r=Text.prototype;hl=ia(t,"firstChild").get,gl=ia(t,"nextSibling").get,ci(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),ci(r)&&(r.__t=void 0)}}function Tn(e=""){return document.createTextNode(e)}function Vn(e){return hl.call(e)}function zs(e){return gl.call(e)}function d(e,t){return Vn(e)}function ee(e,t=!1){{var r=Vn(e);return r instanceof Comment&&r.data===""?zs(r):r}}function m(e,t=1,r=!1){let a=e;for(;t--;)a=zs(a);return a}function Wc(e){e.textContent=""}function xl(){return!1}function Fo(e,t,r){return document.createElementNS(t??Qi,e,void 0)}function Kc(e,t){if(t){const r=document.body;e.autofocus=!0,zn(()=>{document.activeElement===r&&e.focus()})}}let pi=!1;function Yc(){pi||(pi=!0,document.addEventListener("reset",e=>{Promise.resolve().then(()=>{var t;if(!e.defaultPrevented)for(const r of e.target.elements)(t=r.__on_r)==null||t.call(r)})},{capture:!0}))}function Ys(e){var t=Qe,r=Ze;en(null),tn(null);try{return e()}finally{en(t),tn(r)}}function Xc(e,t,r,a=r){e.addEventListener(t,()=>Ys(r));const s=e.__on_r;s?e.__on_r=()=>{s(),a(!0)}:e.__on_r=()=>a(!0),Yc()}function bl(e){Ze===null&&(Qe===null&&tc(),ec()),fa&&Zd()}function Jc(e,t){var r=t.last;r===null?t.last=t.first=e:(r.next=e,e.prev=r,t.last=e)}function gn(e,t){var r=Ze;r!==null&&(r.f&zr)!==0&&(e|=zr);var a={ctx:ur,deps:null,nodes:null,f:e|xr|Qr,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null},s=a;if((e&ts)!==0)Ja!==null?Ja.push(a):Mn(a);else if(t!==null){try{Za(a)}catch(i){throw br(a),i}s.deps===null&&s.teardown===null&&s.nodes===null&&s.first===s.last&&(s.f&ns)===0&&(s=s.first,(e&va)!==0&&(e&Fn)!==0&&s!==null&&(s.f|=Fn))}if(s!==null&&(s.parent=r,r!==null&&Jc(s,r),Qe!==null&&(Qe.f&_r)!==0&&(e&Na)===0)){var o=Qe;(o.effects??(o.effects=[])).push(s)}return a}function Bo(){return Qe!==null&&!pn}function Xs(e){const t=gn(za,null);return Kt(t,gr),t.teardown=e,t}function Dn(e){bl();var t=Ze.f,r=!Qe&&(t&hn)!==0&&(t&rs)===0;if(r){var a=ur;(a.e??(a.e=[])).push(e)}else return _l(e)}function _l(e){return gn(ts|Wi,e)}function Qc(e){return bl(),gn(za|Wi,e)}function Zc(e){da.ensure();const t=gn(Na|ns,e);return(r={})=>new Promise(a=>{r.outro?Ma(t,()=>{br(t),a(void 0)}):(br(t),a(void 0))})}function Go(e){return gn(ts,e)}function eu(e){return gn(Do|ns,e)}function Ho(e,t=0){return gn(za|t,e)}function N(e,t=[],r=[],a=[]){cl(a,t,r,s=>{gn(za,()=>e(...s.map(n)))})}function as(e,t=0){var r=gn(va|t,e);return r}function wl(e,t=0){var r=gn(Ws|t,e);return r}function Or(e){return gn(hn|ns,e)}function yl(e){var t=e.teardown;if(t!==null){const r=fa,a=Qe;mi(!0),en(null);try{t.call(null)}finally{mi(r),en(a)}}}function Uo(e,t=!1){var r=e.first;for(e.first=e.last=null;r!==null;){const s=r.ac;s!==null&&Ys(()=>{s.abort(xa)});var a=r.next;(r.f&Na)!==0?r.parent=null:br(r,t),r=a}}function tu(e){for(var t=e.first;t!==null;){var r=t.next;(t.f&hn)===0&&br(t),t=r}}function br(e,t=!0){var r=!1;(t||(e.f&Yd)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(kl(e.nodes.start,e.nodes.end),r=!0),Uo(e,t&&!r),ks(e,0),Kt(e,En);var a=e.nodes&&e.nodes.t;if(a!==null)for(const o of a)o.stop();yl(e);var s=e.parent;s!==null&&s.first!==null&&Cl(e),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function kl(e,t){for(;e!==null;){var r=e===t?null:zs(e);e.remove(),e=r}}function Cl(e){var t=e.parent,r=e.prev,a=e.next;r!==null&&(r.next=a),a!==null&&(a.prev=r),t!==null&&(t.first===e&&(t.first=a),t.last===e&&(t.last=r))}function Ma(e,t,r=!0){var a=[];Sl(e,a,!0);var s=()=>{r&&br(e),t&&t()},o=a.length;if(o>0){var i=()=>--o||s();for(var l of a)l.out(i)}else s()}function Sl(e,t,r){if((e.f&zr)===0){e.f^=zr;var a=e.nodes&&e.nodes.t;if(a!==null)for(const l of a)(l.is_global||r)&&t.push(l);for(var s=e.first;s!==null;){var o=s.next,i=(s.f&Fn)!==0||(s.f&hn)!==0&&(e.f&va)!==0;Sl(s,t,i?r:!1),s=o}}}function Wo(e){Ml(e,!0)}function Ml(e,t){if((e.f&zr)!==0){e.f^=zr;for(var r=e.first;r!==null;){var a=r.next,s=(r.f&Fn)!==0||(r.f&hn)!==0;Ml(r,s?t:!1),r=a}var o=e.nodes&&e.nodes.t;if(o!==null)for(const i of o)(i.is_global||t)&&i.in()}}function Ko(e,t){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end;r!==null;){var s=r===a?null:zs(r);t.append(r),r=s}}let Vs=!1,fa=!1;function mi(e){fa=e}let Qe=null,pn=!1;function en(e){Qe=e}let Ze=null;function tn(e){Ze=e}let Zr=null;function El(e){Qe!==null&&(Zr===null?Zr=[e]:Zr.push(e))}let Lr=null,Br=0,Xr=null;function ru(e){Xr=e}let Al=1,_a=0,Ea=_a;function hi(e){Ea=e}function zl(){return++Al}function Ts(e){var t=e.f;if((t&xr)!==0)return!0;if(t&_r&&(e.f&=~Ta),(t&mn)!==0){for(var r=e.deps,a=r.length,s=0;s<a;s++){var o=r[s];if(Ts(o)&&ul(o),o.wv>e.wv)return!0}(t&Qr)!==0&&hr===null&&Kt(e,gr)}return!1}function Tl(e,t,r=!0){var a=e.reactions;if(a!==null&&!(Zr!==null&&Ya.call(Zr,e)))for(var s=0;s<a.length;s++){var o=a[s];(o.f&_r)!==0?Tl(o,t,!1):t===o&&(r?Kt(o,xr):(o.f&gr)!==0&&Kt(o,mn),Mn(o))}}function Il(e){var I;var t=Lr,r=Br,a=Xr,s=Qe,o=Zr,i=ur,l=pn,c=Ea,f=e.f;Lr=null,Br=0,Xr=null,Qe=(f&(hn|Na))===0?e:null,Zr=null,Xa(e.ctx),pn=!1,Ea=++_a,e.ac!==null&&(Ys(()=>{e.ac.abort(xa)}),e.ac=null);try{e.f|=mo;var p=e.fn,b=p();e.f|=rs;var _=e.deps,z=He==null?void 0:He.is_fork;if(Lr!==null){var y;if(z||ks(e,Br),_!==null&&Br>0)for(_.length=Br+Lr.length,y=0;y<Lr.length;y++)_[Br+y]=Lr[y];else e.deps=_=Lr;if(Bo()&&(e.f&Qr)!==0)for(y=Br;y<_.length;y++)((I=_[y]).reactions??(I.reactions=[])).push(e)}else!z&&_!==null&&Br<_.length&&(ks(e,Br),_.length=Br);if(Es()&&Xr!==null&&!pn&&_!==null&&(e.f&(_r|mn|xr))===0)for(y=0;y<Xr.length;y++)Tl(Xr[y],e);if(s!==null&&s!==e){if(_a++,s.deps!==null)for(let k=0;k<r;k+=1)s.deps[k].rv=_a;if(t!==null)for(const k of t)k.rv=_a;Xr!==null&&(a===null?a=Xr:a.push(...Xr))}return(e.f&la)!==0&&(e.f^=la),b}catch(k){return nl(k)}finally{e.f^=mo,Lr=t,Br=r,Xr=a,Qe=s,Zr=o,Xa(i),pn=l,Ea=c}}function nu(e,t){let r=t.reactions;if(r!==null){var a=Bd.call(r,e);if(a!==-1){var s=r.length-1;s===0?r=t.reactions=null:(r[a]=r[s],r.pop())}}if(r===null&&(t.f&_r)!==0&&(Lr===null||!Ya.call(Lr,t))){var o=t;(o.f&Qr)!==0&&(o.f^=Qr,o.f&=~Ta),jo(o),Fc(o),ks(o,0)}}function ks(e,t){var r=e.deps;if(r!==null)for(var a=t;a<r.length;a++)nu(e,r[a])}function Za(e){var t=e.f;if((t&En)===0){Kt(e,gr);var r=Ze,a=Vs;Ze=e,Vs=!0;try{(t&(va|Ws))!==0?tu(e):Uo(e),yl(e);var s=Il(e);e.teardown=typeof s=="function"?s:null,e.wv=Al;var o;fo&&kc&&(e.f&xr)!==0&&e.deps}finally{Vs=a,Ze=r}}}async function au(){await Promise.resolve(),Ac()}function n(e){var t=e.f,r=(t&_r)!==0;if(Qe!==null&&!pn){var a=Ze!==null&&(Ze.f&En)!==0;if(!a&&(Zr===null||!Ya.call(Zr,e))){var s=Qe.deps;if((Qe.f&mo)!==0)e.rv<_a&&(e.rv=_a,Lr===null&&s!==null&&s[Br]===e?Br++:Lr===null?Lr=[e]:Lr.push(e));else{(Qe.deps??(Qe.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[Qe]:Ya.call(o,Qe)||o.push(Qe)}}}if(fa&&ca.has(e))return ca.get(e);if(r){var i=e;if(fa){var l=i.v;return((i.f&gr)===0&&i.reactions!==null||Nl(i))&&(l=qo(i)),ca.set(i,l),l}var c=(i.f&Qr)===0&&!pn&&Qe!==null&&(Vs||(Qe.f&Qr)!==0),f=(i.f&rs)===0;Ts(i)&&(c&&(i.f|=Qr),ul(i)),c&&!f&&(fl(i),Pl(i))}if(hr!=null&&hr.has(e))return hr.get(e);if((e.f&la)!==0)throw e.v;return e.v}function Pl(e){if(e.f|=Qr,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&_r)!==0&&(t.f&Qr)===0&&(fl(t),Pl(t))}function Nl(e){if(e.v===cr)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(ca.has(t)||(t.f&_r)!==0&&Nl(t))return!0;return!1}function Ia(e){var t=pn;try{return pn=!0,e()}finally{pn=t}}function ga(e){if(!(typeof e!="object"||!e||e instanceof EventTarget)){if(An in e)Mo(e);else if(!Array.isArray(e))for(let t in e){const r=e[t];typeof r=="object"&&r&&An in r&&Mo(r)}}}function Mo(e,t=new Set){if(typeof e=="object"&&e!==null&&!(e instanceof EventTarget)&&!t.has(e)){t.add(e),e instanceof Date&&e.getTime();for(let a in e)try{Mo(e[a],t)}catch{}const r=Ro(e);if(r!==Object.prototype&&r!==Array.prototype&&r!==Map.prototype&&r!==Set.prototype&&r!==Date.prototype){const a=Gi(r);for(let s in a){const o=a[s].get;if(o)try{o.call(e)}catch{}}}}}function su(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const ou=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function iu(e){return ou.includes(e)}const lu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function du(e){return e=e.toLowerCase(),lu[e]??e}const cu=["touchstart","touchmove"];function uu(e){return cu.includes(e)}const wa=Symbol("events"),$l=new Set,Eo=new Set;function Ll(e,t,r,a={}){function s(o){if(a.capture||Ao.call(t,o),!o.cancelBubble)return Ys(()=>r==null?void 0:r.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?zn(()=>{t.addEventListener(e,s,a)}):t.addEventListener(e,s,a),s}function Va(e,t,r,a,s){var o={capture:a,passive:s},i=Ll(e,t,r,o);(t===document.body||t===window||t===document||t instanceof HTMLMediaElement)&&Xs(()=>{t.removeEventListener(e,i,o)})}function ae(e,t,r){(t[wa]??(t[wa]={}))[e]=r}function Bn(e){for(var t=0;t<e.length;t++)$l.add(e[t]);for(var r of Eo)r(e)}let gi=null;function Ao(e){var k,C;var t=this,r=t.ownerDocument,a=e.type,s=((k=e.composedPath)==null?void 0:k.call(e))||[],o=s[0]||e.target;gi=e;var i=0,l=gi===e&&e[wa];if(l){var c=s.indexOf(l);if(c!==-1&&(t===document||t===window)){e[wa]=t;return}var f=s.indexOf(t);if(f===-1)return;c<=f&&(i=c)}if(o=s[i]||e.target,o!==t){Gd(e,"currentTarget",{configurable:!0,get(){return o||r}});var p=Qe,b=Ze;en(null),tn(null);try{for(var _,z=[];o!==null;){var y=o.assignedSlot||o.parentNode||o.host||null;try{var I=(C=o[wa])==null?void 0:C[a];I!=null&&(!o.disabled||e.target===o)&&I.call(o,e)}catch(L){_?z.push(L):_=L}if(e.cancelBubble||y===t||y===null)break;o=y}if(_){for(let L of z)queueMicrotask(()=>{throw L});throw _}}finally{e[wa]=t,delete e.currentTarget,en(p),tn(b)}}}var Fi;const ao=((Fi=globalThis==null?void 0:globalThis.window)==null?void 0:Fi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function fu(e){return(ao==null?void 0:ao.createHTML(e))??e}function Ol(e){var t=Fo("template");return t.innerHTML=fu(e.replaceAll("<!>","<!---->")),t.content}function Pa(e,t){var r=Ze;r.nodes===null&&(r.nodes={start:e,end:t,a:null,t:null})}function h(e,t){var r=(t&hc)!==0,a=(t&gc)!==0,s,o=!e.startsWith("<!>");return()=>{s===void 0&&(s=Ol(o?e:"<!>"+e),r||(s=Vn(s)));var i=a||ml?document.importNode(s,!0):s.cloneNode(!0);if(r){var l=Vn(i),c=i.lastChild;Pa(l,c)}else Pa(i,i);return i}}function vu(e,t,r="svg"){var a=!e.startsWith("<!>"),s=`<${r}>${a?e:"<!>"+e}</${r}>`,o;return()=>{if(!o){var i=Ol(s),l=Vn(i);o=Vn(l)}var c=o.cloneNode(!0);return Pa(c,c),c}}function pu(e,t){return vu(e,t,"svg")}function ta(e=""){{var t=Tn(e+"");return Pa(t,t),t}}function ye(){var e=document.createDocumentFragment(),t=document.createComment(""),r=Tn();return e.append(t,r),Pa(t,r),e}function v(e,t){e!==null&&e.before(t)}function P(e,t){var r=t==null?"":typeof t=="object"?`${t}`:t;r!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=r,e.nodeValue=`${r}`)}function mu(e,t){return hu(e,t)}const $s=new Map;function hu(e,{target:t,anchor:r,props:a={},events:s,context:o,intro:i=!0,transformError:l}){Uc();var c=void 0,f=Zc(()=>{var p=r??t.appendChild(Tn());Pc(p,{pending:()=>{}},z=>{rn({});var y=ur;o&&(y.c=o),s&&(a.$$events=s),c=e(z,a)||{},nn()},l);var b=new Set,_=z=>{for(var y=0;y<z.length;y++){var I=z[y];if(!b.has(I)){b.add(I);var k=uu(I);for(const U of[t,document]){var C=$s.get(U);C===void 0&&(C=new Map,$s.set(U,C));var L=C.get(I);L===void 0?(U.addEventListener(I,Ao,{passive:k}),C.set(I,1)):C.set(I,L+1)}}}};return _(Us($l)),Eo.add(_),()=>{var k;for(var z of b)for(const C of[t,document]){var y=$s.get(C),I=y.get(z);--I==0?(C.removeEventListener(z,Ao),y.delete(z),y.size===0&&$s.delete(C)):y.set(z,I)}Eo.delete(_),p!==r&&((k=p.parentNode)==null||k.removeChild(p))}});return gu.set(c,f),c}let gu=new WeakMap;var fn,Cn,Hr,Sa,Cs,Ss,Hs;class Js{constructor(t,r=!0){dn(this,"anchor");et(this,fn,new Map);et(this,Cn,new Map);et(this,Hr,new Map);et(this,Sa,new Set);et(this,Cs,!0);et(this,Ss,t=>{if(M(this,fn).has(t)){var r=M(this,fn).get(t),a=M(this,Cn).get(r);if(a)Wo(a),M(this,Sa).delete(r);else{var s=M(this,Hr).get(r);s&&(s.effect.f&zr)===0&&(M(this,Cn).set(r,s.effect),M(this,Hr).delete(r),s.fragment.lastChild.remove(),this.anchor.before(s.fragment),a=s.effect)}for(const[o,i]of M(this,fn)){if(M(this,fn).delete(o),o===t)break;const l=M(this,Hr).get(i);l&&(br(l.effect),M(this,Hr).delete(i))}for(const[o,i]of M(this,Cn)){if(o===r||M(this,Sa).has(o)||(i.f&zr)!==0)continue;const l=()=>{if(Array.from(M(this,fn).values()).includes(o)){var f=document.createDocumentFragment();Ko(i,f),f.append(Tn()),M(this,Hr).set(o,{effect:i,fragment:f})}else br(i);M(this,Sa).delete(o),M(this,Cn).delete(o)};M(this,Cs)||!a?(M(this,Sa).add(o),Ma(i,l,!1)):l()}}});et(this,Hs,t=>{M(this,fn).delete(t);const r=Array.from(M(this,fn).values());for(const[a,s]of M(this,Hr))r.includes(a)||(br(s.effect),M(this,Hr).delete(a))});this.anchor=t,Ge(this,Cs,r)}ensure(t,r){var a=He,s=xl();if(r&&!M(this,Cn).has(t)&&!M(this,Hr).has(t))if(s){var o=document.createDocumentFragment(),i=Tn();o.append(i),M(this,Hr).set(t,{effect:Or(()=>r(i)),fragment:o})}else M(this,Cn).set(t,Or(()=>r(this.anchor)));if(M(this,fn).set(a,t),s){for(const[l,c]of M(this,Cn))l===t?a.unskip_effect(c):a.skip_effect(c);for(const[l,c]of M(this,Hr))l===t?a.unskip_effect(c.effect):a.skip_effect(c.effect);a.oncommit(M(this,Ss)),a.ondiscard(M(this,Hs))}else M(this,Ss).call(this,a)}}fn=new WeakMap,Cn=new WeakMap,Hr=new WeakMap,Sa=new WeakMap,Cs=new WeakMap,Ss=new WeakMap,Hs=new WeakMap;function E(e,t,r=!1){var a=new Js(e),s=r?Fn:0;function o(i,l){a.ensure(i,l)}as(()=>{var i=!1;t((l,c=0)=>{i=!0,o(c,l)}),i||o(-1,null)},s)}function Te(e,t){return t}function xu(e,t,r){for(var a=[],s=t.length,o,i=t.length,l=0;l<s;l++){let b=t[l];Ma(b,()=>{if(o){if(o.pending.delete(b),o.done.add(b),o.pending.size===0){var _=e.outrogroups;zo(e,Us(o.done)),_.delete(o),_.size===0&&(e.outrogroups=null)}}else i-=1},!1)}if(i===0){var c=a.length===0&&r!==null;if(c){var f=r,p=f.parentNode;Wc(p),p.append(f),e.items.clear()}zo(e,t,!c)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function zo(e,t,r=!0){var a;if(e.pending.size>0){a=new Set;for(const i of e.pending.values())for(const l of i)a.add(e.items.get(l).e)}for(var s=0;s<t.length;s++){var o=t[s];if(a!=null&&a.has(o)){o.f|=Sn;const i=document.createDocumentFragment();Ko(o,i)}else br(t[s],r)}}var xi;function Ie(e,t,r,a,s,o=null){var i=e,l=new Map,c=(t&Xi)!==0;if(c){var f=e;i=f.appendChild(Tn())}var p=null,b=Vo(()=>{var U=r();return Oo(U)?U:U==null?[]:Us(U)}),_,z=new Map,y=!0;function I(U){(L.effect.f&En)===0&&(L.pending.delete(U),L.fallback=p,bu(L,_,i,t,a),p!==null&&(_.length===0?(p.f&Sn)===0?Wo(p):(p.f^=Sn,hs(p,null,i)):Ma(p,()=>{p=null})))}function k(U){L.pending.delete(U)}var C=as(()=>{_=n(b);for(var U=_.length,S=new Set,q=He,le=xl(),$=0;$<U;$+=1){var x=_[$],H=a(x,$),te=y?null:l.get(H);te?(te.v&&Qa(te.v,x),te.i&&Qa(te.i,$),le&&q.unskip_effect(te.e)):(te=_u(l,y?i:xi??(xi=Tn()),x,H,$,s,t,r),y||(te.e.f|=Sn),l.set(H,te)),S.add(H)}if(U===0&&o&&!p&&(y?p=Or(()=>o(i)):(p=Or(()=>o(xi??(xi=Tn()))),p.f|=Sn)),U>S.size&&Qd(),!y)if(z.set(q,S),le){for(const[K,T]of l)S.has(K)||q.skip_effect(T.e);q.oncommit(I),q.ondiscard(k)}else I(q);n(b)}),L={effect:C,items:l,pending:z,outrogroups:null,fallback:p};y=!1}function ds(e){for(;e!==null&&(e.f&hn)===0;)e=e.next;return e}function bu(e,t,r,a,s){var te,K,T,ie,fe,be,ve,Ae,me;var o=(a&cc)!==0,i=t.length,l=e.items,c=ds(e.effect.first),f,p=null,b,_=[],z=[],y,I,k,C;if(o)for(C=0;C<i;C+=1)y=t[C],I=s(y,C),k=l.get(I).e,(k.f&Sn)===0&&((K=(te=k.nodes)==null?void 0:te.a)==null||K.measure(),(b??(b=new Set)).add(k));for(C=0;C<i;C+=1){if(y=t[C],I=s(y,C),k=l.get(I).e,e.outrogroups!==null)for(const he of e.outrogroups)he.pending.delete(k),he.done.delete(k);if((k.f&Sn)!==0)if(k.f^=Sn,k===c)hs(k,null,r);else{var L=p?p.next:c;k===e.effect.last&&(e.effect.last=k.prev),k.prev&&(k.prev.next=k.next),k.next&&(k.next.prev=k.prev),Qn(e,p,k),Qn(e,k,L),hs(k,L,r),p=k,_=[],z=[],c=ds(p.next);continue}if((k.f&zr)!==0&&(Wo(k),o&&((ie=(T=k.nodes)==null?void 0:T.a)==null||ie.unfix(),(b??(b=new Set)).delete(k))),k!==c){if(f!==void 0&&f.has(k)){if(_.length<z.length){var U=z[0],S;p=U.prev;var q=_[0],le=_[_.length-1];for(S=0;S<_.length;S+=1)hs(_[S],U,r);for(S=0;S<z.length;S+=1)f.delete(z[S]);Qn(e,q.prev,le.next),Qn(e,p,q),Qn(e,le,U),c=U,p=le,C-=1,_=[],z=[]}else f.delete(k),hs(k,c,r),Qn(e,k.prev,k.next),Qn(e,k,p===null?e.effect.first:p.next),Qn(e,p,k),p=k;continue}for(_=[],z=[];c!==null&&c!==k;)(f??(f=new Set)).add(c),z.push(c),c=ds(c.next);if(c===null)continue}(k.f&Sn)===0&&_.push(k),p=k,c=ds(k.next)}if(e.outrogroups!==null){for(const he of e.outrogroups)he.pending.size===0&&(zo(e,Us(he.done)),(fe=e.outrogroups)==null||fe.delete(he));e.outrogroups.size===0&&(e.outrogroups=null)}if(c!==null||f!==void 0){var $=[];if(f!==void 0)for(k of f)(k.f&zr)===0&&$.push(k);for(;c!==null;)(c.f&zr)===0&&c!==e.fallback&&$.push(c),c=ds(c.next);var x=$.length;if(x>0){var H=(a&Xi)!==0&&i===0?r:null;if(o){for(C=0;C<x;C+=1)(ve=(be=$[C].nodes)==null?void 0:be.a)==null||ve.measure();for(C=0;C<x;C+=1)(me=(Ae=$[C].nodes)==null?void 0:Ae.a)==null||me.fix()}xu(e,$,H)}}o&&zn(()=>{var he,W;if(b!==void 0)for(k of b)(W=(he=k.nodes)==null?void 0:he.a)==null||W.apply()})}function _u(e,t,r,a,s,o,i,l){var c=(i&lc)!==0?(i&uc)===0?Bc(r,!1,!1):ua(r):null,f=(i&dc)!==0?ua(s):null;return{v:c,i:f,e:Or(()=>(o(t,c??r,f??s,l),()=>{e.delete(a)}))}}function hs(e,t,r){if(e.nodes)for(var a=e.nodes.start,s=e.nodes.end,o=t&&(t.f&Sn)===0?t.nodes.start:r;a!==null;){var i=zs(a);if(o.before(a),a===s)return;a=i}}function Qn(e,t,r){t===null?e.effect.first=r:t.next=r,r===null?e.effect.last=t:r.prev=t}function oa(e,t,r=!1,a=!1,s=!1){var o=e,i="";N(()=>{var l=Ze;if(i!==(i=t()??"")&&(l.nodes!==null&&(kl(l.nodes.start,l.nodes.end),l.nodes=null),i!=="")){var c=r?Zi:a?xc:void 0,f=Fo(r?"svg":a?"math":"template",c);f.innerHTML=i;var p=r||a?f:f.content;if(Pa(Vn(p),p.lastChild),r||a)for(;Vn(p);)o.before(Vn(p));else o.before(p)}})}function Ue(e,t,r,a,s){var l;var o=(l=t.$$slots)==null?void 0:l[r],i=!1;o===!0&&(o=t.children,i=!0),o===void 0||o(e,i?()=>a:a)}function To(e,t,...r){var a=new Js(e);as(()=>{const s=t()??null;a.ensure(s,s&&(o=>s(o,...r)))},Fn)}function wu(e,t,r){var a=new Js(e);as(()=>{var s=t()??null;a.ensure(s,s&&(o=>r(o,s)))},Fn)}function yu(e,t,r,a,s,o){var i=null,l=e,c=new Js(l,!1);as(()=>{const f=t()||null;var p=Zi;if(f===null){c.ensure(null,null);return}return c.ensure(f,b=>{if(f){if(i=Fo(f,p),Pa(i,i),a){var _=i.appendChild(Tn());a(i,_)}Ze.nodes.end=i,b.before(i)}}),()=>{}},Fn),Xs(()=>{})}function ku(e,t){var r=void 0,a;wl(()=>{r!==(r=t())&&(a&&(br(a),a=null),r&&(a=Or(()=>{Go(()=>r(e))})))})}function Rl(e){var t,r,a="";if(typeof e=="string"||typeof e=="number")a+=e;else if(typeof e=="object")if(Array.isArray(e)){var s=e.length;for(t=0;t<s;t++)e[t]&&(r=Rl(e[t]))&&(a&&(a+=" "),a+=r)}else for(r in e)e[r]&&(a&&(a+=" "),a+=r);return a}function Dl(){for(var e,t,r=0,a="",s=arguments.length;r<s;r++)(e=arguments[r])&&(t=Rl(e))&&(a&&(a+=" "),a+=t);return a}function Pt(e){return typeof e=="object"?Dl(e):e??""}const bi=[...` 	
\r\f \v\uFEFF`];function Cu(e,t,r){var a=e==null?"":""+e;if(t&&(a=a?a+" "+t:t),r){for(var s of Object.keys(r))if(r[s])a=a?a+" "+s:s;else if(a.length)for(var o=s.length,i=0;(i=a.indexOf(s,i))>=0;){var l=i+o;(i===0||bi.includes(a[i-1]))&&(l===a.length||bi.includes(a[l]))?a=(i===0?"":a.substring(0,i))+a.substring(l+1):i=l}}return a===""?null:a}function _i(e,t=!1){var r=t?" !important;":";",a="";for(var s of Object.keys(e)){var o=e[s];o!=null&&o!==""&&(a+=" "+s+": "+o+r)}return a}function so(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Su(e,t){if(t){var r="",a,s;if(Array.isArray(t)?(a=t[0],s=t[1]):a=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,i=0,l=!1,c=[];a&&c.push(...Object.keys(a).map(so)),s&&c.push(...Object.keys(s).map(so));var f=0,p=-1;const I=e.length;for(var b=0;b<I;b++){var _=e[b];if(l?_==="/"&&e[b-1]==="*"&&(l=!1):o?o===_&&(o=!1):_==="/"&&e[b+1]==="*"?l=!0:_==='"'||_==="'"?o=_:_==="("?i++:_===")"&&i--,!l&&o===!1&&i===0){if(_===":"&&p===-1)p=b;else if(_===";"||b===I-1){if(p!==-1){var z=so(e.substring(f,p).trim());if(!c.includes(z)){_!==";"&&b++;var y=e.substring(f,b).trim();r+=" "+y+";"}}f=b+1,p=-1}}}}return a&&(r+=_i(a)),s&&(r+=_i(s,!0)),r=r.trim(),r===""?null:r}return e==null?null:String(e)}function Le(e,t,r,a,s,o){var i=e.__className;if(i!==r||i===void 0){var l=Cu(r,a,o);l==null?e.removeAttribute("class"):t?e.className=l:e.setAttribute("class",l),e.__className=r}else if(o&&s!==o)for(var c in o){var f=!!o[c];(s==null||f!==!!s[c])&&e.classList.toggle(c,f)}return o}function oo(e,t={},r,a){for(var s in r){var o=r[s];t[s]!==o&&(r[s]==null?e.style.removeProperty(s):e.style.setProperty(s,o,a))}}function Io(e,t,r,a){var s=e.__style;if(s!==t){var o=Su(t,a);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else a&&(Array.isArray(a)?(oo(e,r==null?void 0:r[0],a[0]),oo(e,r==null?void 0:r[1],a[1],"important")):oo(e,r,a));return a}function Po(e,t,r=!1){if(e.multiple){if(t==null)return;if(!Oo(t))return _c();for(var a of e.options)a.selected=t.includes(wi(a));return}for(a of e.options){var s=wi(a);if(Hc(s,t)){a.selected=!0;return}}(!r||t!==void 0)&&(e.selectedIndex=-1)}function Mu(e){var t=new MutationObserver(()=>{Po(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Xs(()=>{t.disconnect()})}function wi(e){return"__value"in e?e.__value:e.value}const cs=Symbol("class"),us=Symbol("style"),jl=Symbol("is custom element"),Vl=Symbol("is html"),Eu=Yi?"option":"OPTION",Au=Yi?"select":"SELECT";function zu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function qn(e,t,r,a){var s=ql(e);s[t]!==(s[t]=r)&&(t==="loading"&&(e[Xd]=r),r==null?e.removeAttribute(t):typeof r!="string"&&Fl(e).includes(t)?e[t]=r:e.setAttribute(t,r))}function Tu(e,t,r,a,s=!1,o=!1){var i=ql(e),l=i[jl],c=!i[Vl],f=t||{},p=e.nodeName===Eu;for(var b in t)b in r||(r[b]=null);r.class?r.class=Pt(r.class):r[cs]&&(r.class=null),r[us]&&(r.style??(r.style=null));var _=Fl(e);for(const S in r){let q=r[S];if(p&&S==="value"&&q==null){e.value=e.__value="",f[S]=q;continue}if(S==="class"){var z=e.namespaceURI==="http://www.w3.org/1999/xhtml";Le(e,z,q,a,t==null?void 0:t[cs],r[cs]),f[S]=q,f[cs]=r[cs];continue}if(S==="style"){Io(e,q,t==null?void 0:t[us],r[us]),f[S]=q,f[us]=r[us];continue}var y=f[S];if(!(q===y&&!(q===void 0&&e.hasAttribute(S)))){f[S]=q;var I=S[0]+S[1];if(I!=="$$")if(I==="on"){const le={},$="$$"+S;let x=S.slice(2);var k=iu(x);if(su(x)&&(x=x.slice(0,-7),le.capture=!0),!k&&y){if(q!=null)continue;e.removeEventListener(x,f[$],le),f[$]=null}if(k)ae(x,e,q),Bn([x]);else if(q!=null){let H=function(te){f[S].call(this,te)};var U=H;f[$]=Ll(x,e,H,le)}}else if(S==="style")qn(e,S,q);else if(S==="autofocus")Kc(e,!!q);else if(!l&&(S==="__value"||S==="value"&&q!=null))e.value=e.__value=q;else if(S==="selected"&&p)zu(e,q);else{var C=S;c||(C=du(C));var L=C==="defaultValue"||C==="defaultChecked";if(q==null&&!l&&!L)if(i[S]=null,C==="value"||C==="checked"){let le=e;const $=t===void 0;if(C==="value"){let x=le.defaultValue;le.removeAttribute(C),le.defaultValue=x,le.value=le.__value=$?x:null}else{let x=le.defaultChecked;le.removeAttribute(C),le.defaultChecked=x,le.checked=$?x:!1}}else e.removeAttribute(S);else L||_.includes(C)&&(l||typeof q!="string")?(e[C]=q,C in i&&(i[C]=cr)):typeof q!="function"&&qn(e,C,q)}}}return f}function qs(e,t,r=[],a=[],s=[],o,i=!1,l=!1){cl(s,r,a,c=>{var f=void 0,p={},b=e.nodeName===Au,_=!1;if(wl(()=>{var y=t(...c.map(n)),I=Tu(e,f,y,o,i,l);_&&b&&"value"in y&&Po(e,y.value);for(let C of Object.getOwnPropertySymbols(p))y[C]||br(p[C]);for(let C of Object.getOwnPropertySymbols(y)){var k=y[C];C.description===bc&&(!f||k!==f[C])&&(p[C]&&br(p[C]),p[C]=Or(()=>ku(e,()=>k))),I[C]=k}f=I}),b){var z=e;Go(()=>{Po(z,f.value,!0),Mu(z)})}_=!0})}function ql(e){return e.__attributes??(e.__attributes={[jl]:e.nodeName.includes("-"),[Vl]:e.namespaceURI===Qi})}var yi=new Map;function Fl(e){var t=e.getAttribute("is")||e.nodeName,r=yi.get(t);if(r)return r;yi.set(t,r=[]);for(var a,s=e,o=Element.prototype;o!==s;){a=Gi(s);for(var i in a)a[i].set&&r.push(i);s=Ro(s)}return r}function ja(e,t,r=t){var a=new WeakSet;Xc(e,"input",async s=>{var o=s?e.defaultValue:e.value;if(o=io(e)?lo(o):o,r(o),He!==null&&a.add(He),await au(),o!==(o=t())){var i=e.selectionStart,l=e.selectionEnd,c=e.value.length;if(e.value=o??"",l!==null){var f=e.value.length;i===l&&l===c&&f>c?(e.selectionStart=f,e.selectionEnd=f):(e.selectionStart=i,e.selectionEnd=Math.min(l,f))}}}),Ia(t)==null&&e.value&&(r(io(e)?lo(e.value):e.value),He!==null&&a.add(He)),Ho(()=>{var s=t();if(e===document.activeElement){var o=ho??He;if(a.has(o))return}io(e)&&s===lo(e.value)||e.type==="date"&&!s&&!e.value||s!==e.value&&(e.value=s??"")})}function io(e){var t=e.type;return t==="number"||t==="range"}function lo(e){return e===""?null:+e}function ki(e,t){return e===t||(e==null?void 0:e[An])===t}function Aa(e={},t,r,a){return Go(()=>{var s,o;return Ho(()=>{s=o,o=[],Ia(()=>{e!==r(...o)&&(t(e,...o),s&&ki(r(...s),e)&&t(null,...s))})}),()=>{zn(()=>{o&&ki(r(...o),e)&&t(null,...o)})}}),e}function Iu(e=!1){const t=ur,r=t.l.u;if(!r)return;let a=()=>ga(t.s);if(e){let s=0,o={};const i=As(()=>{let l=!1;const c=t.s;for(const f in c)c[f]!==o[f]&&(o[f]=c[f],l=!0);return l&&s++,s});a=()=>n(i)}r.b.length&&Qc(()=>{Ci(t,a),vo(r.b)}),Dn(()=>{const s=Ia(()=>r.m.map(Kd));return()=>{for(const o of s)typeof o=="function"&&o()}}),r.a.length&&Dn(()=>{Ci(t,a),vo(r.a)})}function Ci(e,t){if(e.l.s)for(const r of e.l.s)n(r);t()}let Ls=!1;function Pu(e){var t=Ls;try{return Ls=!1,[e(),Ls]}finally{Ls=t}}const Nu={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function $u(e,t,r){return new Proxy({props:e,exclude:t},Nu)}const Lu={get(e,t){if(!e.exclude.includes(t))return n(e.version),t in e.special?e.special[t]():e.props[t]},set(e,t,r){if(!(t in e.special)){var a=Ze;try{tn(e.parent_effect),e.special[t]=dt({get[t](){return e.props[t]}},t,Ji)}finally{tn(a)}}return e.special[t](r),xs(e.version),!0},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},deleteProperty(e,t){return e.exclude.includes(t)||(e.exclude.push(t),xs(e.version)),!0},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Ve(e,t){return new Proxy({props:e,exclude:t,special:{},version:ua(0),parent_effect:Ze},Lu)}const Ou={get(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(ls(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a)return a[t]}},set(e,t,r){let a=e.props.length;for(;a--;){let s=e.props[a];ls(s)&&(s=s());const o=ia(s,t);if(o&&o.set)return o.set(r),!0}return!1},getOwnPropertyDescriptor(e,t){let r=e.props.length;for(;r--;){let a=e.props[r];if(ls(a)&&(a=a()),typeof a=="object"&&a!==null&&t in a){const s=ia(a,t);return s&&!s.configurable&&(s.configurable=!0),s}}},has(e,t){if(t===An||t===Ki)return!1;for(let r of e.props)if(ls(r)&&(r=r()),r!=null&&t in r)return!0;return!1},ownKeys(e){const t=[];for(let r of e.props)if(ls(r)&&(r=r()),!!r){for(const a in r)t.includes(a)||t.push(a);for(const a of Object.getOwnPropertySymbols(r))t.includes(a)||t.push(a)}return t}};function Ye(...e){return new Proxy({props:e},Ou)}function dt(e,t,r,a){var U;var s=!Ms||(r&vc)!==0,o=(r&pc)!==0,i=(r&mc)!==0,l=a,c=!0,f=()=>(c&&(c=!1,l=i?Ia(a):a),l),p;if(o){var b=An in e||Ki in e;p=((U=ia(e,t))==null?void 0:U.set)??(b&&t in e?S=>e[t]=S:void 0)}var _,z=!1;o?[_,z]=Pu(()=>e[t]):_=e[t],_===void 0&&a!==void 0&&(_=f(),p&&(s&&nc(),p(_)));var y;if(s?y=()=>{var S=e[t];return S===void 0?f():(c=!0,S)}:y=()=>{var S=e[t];return S!==void 0&&(l=void 0),S===void 0?l:S},s&&(r&Ji)===0)return y;if(p){var I=e.$$legacy;return(function(S,q){return arguments.length>0?((!s||!q||I||z)&&p(q?y():S),S):y()})}var k=!1,C=((r&fc)!==0?As:Vo)(()=>(k=!1,y()));o&&n(C);var L=Ze;return(function(S,q){if(arguments.length>0){const le=q?n(C):s&&o?qt(S):S;return u(C,le),k=!0,l!==void 0&&(l=le),S}return fa&&k||(L.f&En)!==0?C.v:n(C)})}const Ru="5";var Bi;typeof window<"u"&&((Bi=window.__svelte??(window.__svelte={})).v??(Bi.v=new Set)).add(Ru);const In="";async function Du(){const e=await fetch(`${In}/api/status`);if(!e.ok)throw new Error("상태 확인 실패");return e.json()}async function ju(e,t=null,r=null){const a={provider:e};t&&(a.model=t),r&&(a.api_key=r);const s=await fetch(`${In}/api/provider/validate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!s.ok)throw new Error("설정 실패");return s.json()}async function Vu(e){const t=await fetch(`${In}/api/models/${encodeURIComponent(e)}`);return t.ok?t.json():{models:[]}}function qu(e,{onProgress:t,onDone:r,onError:a}){const s=new AbortController;return fetch(`${In}/api/ollama/pull`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:e}),signal:s.signal}).then(async o=>{if(!o.ok){a==null||a("다운로드 실패");return}const i=o.body.getReader(),l=new TextDecoder;let c="";for(;;){const{done:f,value:p}=await i.read();if(f)break;c+=l.decode(p,{stream:!0});const b=c.split(`
`);c=b.pop()||"";for(const _ of b)if(_.startsWith("data:"))try{const z=JSON.parse(_.slice(5).trim());z.total&&z.completed!==void 0?t==null||t({total:z.total,completed:z.completed,status:z.status}):z.status&&(t==null||t({status:z.status}))}catch{}}r==null||r()}).catch(o=>{o.name!=="AbortError"&&(a==null||a(o.message))}),{abort:()=>s.abort()}}async function Fu(){const e=await fetch(`${In}/api/codex/logout`,{method:"POST"});if(!e.ok)throw new Error("Codex 로그아웃 실패");return e.json()}async function Bu(e,t=null,r=null){let a=`${In}/api/export/excel/${encodeURIComponent(e)}`;const s=new URLSearchParams;r?s.set("template_id",r):t&&t.length>0&&s.set("modules",t.join(","));const o=s.toString();o&&(a+=`?${o}`);const i=await fetch(a);if(!i.ok){const _=await i.json().catch(()=>({}));throw new Error(_.detail||"Excel 다운로드 실패")}const l=await i.blob(),f=(i.headers.get("content-disposition")||"").match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i),p=f?decodeURIComponent(f[1]):`${e}.xlsx`,b=document.createElement("a");return b.href=URL.createObjectURL(l),b.download=p,b.click(),URL.revokeObjectURL(b.href),p}async function Bl(e){const t=await fetch(`${In}/api/search?q=${encodeURIComponent(e)}`);if(!t.ok)throw new Error("검색 실패");return t.json()}async function Gu(e,t){const r=await fetch(`${In}/api/company/${e}/show/${encodeURIComponent(t)}/all`);if(!r.ok)throw new Error("company topic 일괄 조회 실패");return r.json()}async function Hu(e){const t=await fetch(`${In}/api/company/${e}/sections`);if(!t.ok)throw new Error("sections 조회 실패");return t.json()}function Uu(e,t,r={},{onMeta:a,onSnapshot:s,onContext:o,onSystemPrompt:i,onToolCall:l,onToolResult:c,onChunk:f,onDone:p,onError:b},_=null){const z={question:t,stream:!0,...r};e&&(z.company=e),_&&_.length>0&&(z.history=_);const y=new AbortController;return fetch(`${In}/api/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(z),signal:y.signal}).then(async I=>{if(!I.ok){const q=await I.json().catch(()=>({}));b==null||b(q.detail||"스트리밍 실패");return}const k=I.body.getReader(),C=new TextDecoder;let L="",U=!1,S=null;for(;;){const{done:q,value:le}=await k.read();if(q)break;L+=C.decode(le,{stream:!0});const $=L.split(`
`);L=$.pop()||"";for(const x of $)if(x.startsWith("event:"))S=x.slice(6).trim();else if(x.startsWith("data:")&&S){const H=x.slice(5).trim();try{const te=JSON.parse(H);S==="meta"?a==null||a(te):S==="snapshot"?s==null||s(te):S==="context"?o==null||o(te):S==="system_prompt"?i==null||i(te):S==="tool_call"?l==null||l(te):S==="tool_result"?c==null||c(te):S==="chunk"?f==null||f(te.text):S==="error"?b==null||b(te.error,te.action,te.detail):S==="done"&&(U||(U=!0,p==null||p()))}catch{}S=null}}U||(U=!0,p==null||p())}).catch(I=>{I.name!=="AbortError"&&(b==null||b(I.message))}),{abort:()=>y.abort()}}const Wu=(e,t)=>{const r=new Array(e.length+t.length);for(let a=0;a<e.length;a++)r[a]=e[a];for(let a=0;a<t.length;a++)r[e.length+a]=t[a];return r},Ku=(e,t)=>({classGroupId:e,validator:t}),Gl=(e=new Map,t=null,r)=>({nextPart:e,validators:t,classGroupId:r}),Fs="-",Si=[],Yu="arbitrary..",Xu=e=>{const t=Qu(e),{conflictingClassGroups:r,conflictingClassGroupModifiers:a}=e;return{getClassGroupId:i=>{if(i.startsWith("[")&&i.endsWith("]"))return Ju(i);const l=i.split(Fs),c=l[0]===""&&l.length>1?1:0;return Hl(l,c,t)},getConflictingClassGroupIds:(i,l)=>{if(l){const c=a[i],f=r[i];return c?f?Wu(f,c):c:f||Si}return r[i]||Si}}},Hl=(e,t,r)=>{if(e.length-t===0)return r.classGroupId;const s=e[t],o=r.nextPart.get(s);if(o){const f=Hl(e,t+1,o);if(f)return f}const i=r.validators;if(i===null)return;const l=t===0?e.join(Fs):e.slice(t).join(Fs),c=i.length;for(let f=0;f<c;f++){const p=i[f];if(p.validator(l))return p.classGroupId}},Ju=e=>e.slice(1,-1).indexOf(":")===-1?void 0:(()=>{const t=e.slice(1,-1),r=t.indexOf(":"),a=t.slice(0,r);return a?Yu+a:void 0})(),Qu=e=>{const{theme:t,classGroups:r}=e;return Zu(r,t)},Zu=(e,t)=>{const r=Gl();for(const a in e){const s=e[a];Yo(s,r,a,t)}return r},Yo=(e,t,r,a)=>{const s=e.length;for(let o=0;o<s;o++){const i=e[o];ef(i,t,r,a)}},ef=(e,t,r,a)=>{if(typeof e=="string"){tf(e,t,r);return}if(typeof e=="function"){rf(e,t,r,a);return}nf(e,t,r,a)},tf=(e,t,r)=>{const a=e===""?t:Ul(t,e);a.classGroupId=r},rf=(e,t,r,a)=>{if(af(e)){Yo(e(a),t,r,a);return}t.validators===null&&(t.validators=[]),t.validators.push(Ku(r,e))},nf=(e,t,r,a)=>{const s=Object.entries(e),o=s.length;for(let i=0;i<o;i++){const[l,c]=s[i];Yo(c,Ul(t,l),r,a)}},Ul=(e,t)=>{let r=e;const a=t.split(Fs),s=a.length;for(let o=0;o<s;o++){const i=a[o];let l=r.nextPart.get(i);l||(l=Gl(),r.nextPart.set(i,l)),r=l}return r},af=e=>"isThemeGetter"in e&&e.isThemeGetter===!0,sf=e=>{if(e<1)return{get:()=>{},set:()=>{}};let t=0,r=Object.create(null),a=Object.create(null);const s=(o,i)=>{r[o]=i,t++,t>e&&(t=0,a=r,r=Object.create(null))};return{get(o){let i=r[o];if(i!==void 0)return i;if((i=a[o])!==void 0)return s(o,i),i},set(o,i){o in r?r[o]=i:s(o,i)}}},No="!",Mi=":",of=[],Ei=(e,t,r,a,s)=>({modifiers:e,hasImportantModifier:t,baseClassName:r,maybePostfixModifierPosition:a,isExternal:s}),lf=e=>{const{prefix:t,experimentalParseClassName:r}=e;let a=s=>{const o=[];let i=0,l=0,c=0,f;const p=s.length;for(let I=0;I<p;I++){const k=s[I];if(i===0&&l===0){if(k===Mi){o.push(s.slice(c,I)),c=I+1;continue}if(k==="/"){f=I;continue}}k==="["?i++:k==="]"?i--:k==="("?l++:k===")"&&l--}const b=o.length===0?s:s.slice(c);let _=b,z=!1;b.endsWith(No)?(_=b.slice(0,-1),z=!0):b.startsWith(No)&&(_=b.slice(1),z=!0);const y=f&&f>c?f-c:void 0;return Ei(o,z,_,y)};if(t){const s=t+Mi,o=a;a=i=>i.startsWith(s)?o(i.slice(s.length)):Ei(of,!1,i,void 0,!0)}if(r){const s=a;a=o=>r({className:o,parseClassName:s})}return a},df=e=>{const t=new Map;return e.orderSensitiveModifiers.forEach((r,a)=>{t.set(r,1e6+a)}),r=>{const a=[];let s=[];for(let o=0;o<r.length;o++){const i=r[o],l=i[0]==="[",c=t.has(i);l||c?(s.length>0&&(s.sort(),a.push(...s),s=[]),a.push(i)):s.push(i)}return s.length>0&&(s.sort(),a.push(...s)),a}},cf=e=>({cache:sf(e.cacheSize),parseClassName:lf(e),sortModifiers:df(e),...Xu(e)}),uf=/\s+/,ff=(e,t)=>{const{parseClassName:r,getClassGroupId:a,getConflictingClassGroupIds:s,sortModifiers:o}=t,i=[],l=e.trim().split(uf);let c="";for(let f=l.length-1;f>=0;f-=1){const p=l[f],{isExternal:b,modifiers:_,hasImportantModifier:z,baseClassName:y,maybePostfixModifierPosition:I}=r(p);if(b){c=p+(c.length>0?" "+c:c);continue}let k=!!I,C=a(k?y.substring(0,I):y);if(!C){if(!k){c=p+(c.length>0?" "+c:c);continue}if(C=a(y),!C){c=p+(c.length>0?" "+c:c);continue}k=!1}const L=_.length===0?"":_.length===1?_[0]:o(_).join(":"),U=z?L+No:L,S=U+C;if(i.indexOf(S)>-1)continue;i.push(S);const q=s(C,k);for(let le=0;le<q.length;++le){const $=q[le];i.push(U+$)}c=p+(c.length>0?" "+c:c)}return c},vf=(...e)=>{let t=0,r,a,s="";for(;t<e.length;)(r=e[t++])&&(a=Wl(r))&&(s&&(s+=" "),s+=a);return s},Wl=e=>{if(typeof e=="string")return e;let t,r="";for(let a=0;a<e.length;a++)e[a]&&(t=Wl(e[a]))&&(r&&(r+=" "),r+=t);return r},pf=(e,...t)=>{let r,a,s,o;const i=c=>{const f=t.reduce((p,b)=>b(p),e());return r=cf(f),a=r.cache.get,s=r.cache.set,o=l,l(c)},l=c=>{const f=a(c);if(f)return f;const p=ff(c,r);return s(c,p),p};return o=i,(...c)=>o(vf(...c))},mf=[],ar=e=>{const t=r=>r[e]||mf;return t.isThemeGetter=!0,t},Kl=/^\[(?:(\w[\w-]*):)?(.+)\]$/i,Yl=/^\((?:(\w[\w-]*):)?(.+)\)$/i,hf=/^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/,gf=/^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/,xf=/\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/,bf=/^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix)\(.+\)$/,_f=/^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/,wf=/^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/,Zn=e=>hf.test(e),je=e=>!!e&&!Number.isNaN(Number(e)),ea=e=>!!e&&Number.isInteger(Number(e)),co=e=>e.endsWith("%")&&je(e.slice(0,-1)),Ln=e=>gf.test(e),Xl=()=>!0,yf=e=>xf.test(e)&&!bf.test(e),Xo=()=>!1,kf=e=>_f.test(e),Cf=e=>wf.test(e),Sf=e=>!ne(e)&&!se(e),Mf=e=>pa(e,Zl,Xo),ne=e=>Kl.test(e),ha=e=>pa(e,ed,yf),Ai=e=>pa(e,$f,je),Ef=e=>pa(e,rd,Xl),Af=e=>pa(e,td,Xo),zi=e=>pa(e,Jl,Xo),zf=e=>pa(e,Ql,Cf),Os=e=>pa(e,nd,kf),se=e=>Yl.test(e),fs=e=>$a(e,ed),Tf=e=>$a(e,td),Ti=e=>$a(e,Jl),If=e=>$a(e,Zl),Pf=e=>$a(e,Ql),Rs=e=>$a(e,nd,!0),Nf=e=>$a(e,rd,!0),pa=(e,t,r)=>{const a=Kl.exec(e);return a?a[1]?t(a[1]):r(a[2]):!1},$a=(e,t,r=!1)=>{const a=Yl.exec(e);return a?a[1]?t(a[1]):r:!1},Jl=e=>e==="position"||e==="percentage",Ql=e=>e==="image"||e==="url",Zl=e=>e==="length"||e==="size"||e==="bg-size",ed=e=>e==="length",$f=e=>e==="number",td=e=>e==="family-name",rd=e=>e==="number"||e==="weight",nd=e=>e==="shadow",Lf=()=>{const e=ar("color"),t=ar("font"),r=ar("text"),a=ar("font-weight"),s=ar("tracking"),o=ar("leading"),i=ar("breakpoint"),l=ar("container"),c=ar("spacing"),f=ar("radius"),p=ar("shadow"),b=ar("inset-shadow"),_=ar("text-shadow"),z=ar("drop-shadow"),y=ar("blur"),I=ar("perspective"),k=ar("aspect"),C=ar("ease"),L=ar("animate"),U=()=>["auto","avoid","all","avoid-page","page","left","right","column"],S=()=>["center","top","bottom","left","right","top-left","left-top","top-right","right-top","bottom-right","right-bottom","bottom-left","left-bottom"],q=()=>[...S(),se,ne],le=()=>["auto","hidden","clip","visible","scroll"],$=()=>["auto","contain","none"],x=()=>[se,ne,c],H=()=>[Zn,"full","auto",...x()],te=()=>[ea,"none","subgrid",se,ne],K=()=>["auto",{span:["full",ea,se,ne]},ea,se,ne],T=()=>[ea,"auto",se,ne],ie=()=>["auto","min","max","fr",se,ne],fe=()=>["start","end","center","between","around","evenly","stretch","baseline","center-safe","end-safe"],be=()=>["start","end","center","stretch","center-safe","end-safe"],ve=()=>["auto",...x()],Ae=()=>[Zn,"auto","full","dvw","dvh","lvw","lvh","svw","svh","min","max","fit",...x()],me=()=>[Zn,"screen","full","dvw","lvw","svw","min","max","fit",...x()],he=()=>[Zn,"screen","full","lh","dvh","lvh","svh","min","max","fit",...x()],W=()=>[e,se,ne],tt=()=>[...S(),Ti,zi,{position:[se,ne]}],ke=()=>["no-repeat",{repeat:["","x","y","space","round"]}],A=()=>["auto","cover","contain",If,Mf,{size:[se,ne]}],re=()=>[co,fs,ha],Y=()=>["","none","full",f,se,ne],X=()=>["",je,fs,ha],ge=()=>["solid","dashed","dotted","double"],Z=()=>["normal","multiply","screen","overlay","darken","lighten","color-dodge","color-burn","hard-light","soft-light","difference","exclusion","hue","saturation","color","luminosity"],oe=()=>[je,co,Ti,zi],ct=()=>["","none",y,se,ne],Bt=()=>["none",je,se,ne],Rt=()=>["none",je,se,ne],wt=()=>[je,se,ne],er=()=>[Zn,"full",...x()];return{cacheSize:500,theme:{animate:["spin","ping","pulse","bounce"],aspect:["video"],blur:[Ln],breakpoint:[Ln],color:[Xl],container:[Ln],"drop-shadow":[Ln],ease:["in","out","in-out"],font:[Sf],"font-weight":["thin","extralight","light","normal","medium","semibold","bold","extrabold","black"],"inset-shadow":[Ln],leading:["none","tight","snug","normal","relaxed","loose"],perspective:["dramatic","near","normal","midrange","distant","none"],radius:[Ln],shadow:[Ln],spacing:["px",je],text:[Ln],"text-shadow":[Ln],tracking:["tighter","tight","normal","wide","wider","widest"]},classGroups:{aspect:[{aspect:["auto","square",Zn,ne,se,k]}],container:["container"],columns:[{columns:[je,ne,se,l]}],"break-after":[{"break-after":U()}],"break-before":[{"break-before":U()}],"break-inside":[{"break-inside":["auto","avoid","avoid-page","avoid-column"]}],"box-decoration":[{"box-decoration":["slice","clone"]}],box:[{box:["border","content"]}],display:["block","inline-block","inline","flex","inline-flex","table","inline-table","table-caption","table-cell","table-column","table-column-group","table-footer-group","table-header-group","table-row-group","table-row","flow-root","grid","inline-grid","contents","list-item","hidden"],sr:["sr-only","not-sr-only"],float:[{float:["right","left","none","start","end"]}],clear:[{clear:["left","right","both","none","start","end"]}],isolation:["isolate","isolation-auto"],"object-fit":[{object:["contain","cover","fill","none","scale-down"]}],"object-position":[{object:q()}],overflow:[{overflow:le()}],"overflow-x":[{"overflow-x":le()}],"overflow-y":[{"overflow-y":le()}],overscroll:[{overscroll:$()}],"overscroll-x":[{"overscroll-x":$()}],"overscroll-y":[{"overscroll-y":$()}],position:["static","fixed","absolute","relative","sticky"],inset:[{inset:H()}],"inset-x":[{"inset-x":H()}],"inset-y":[{"inset-y":H()}],start:[{"inset-s":H(),start:H()}],end:[{"inset-e":H(),end:H()}],"inset-bs":[{"inset-bs":H()}],"inset-be":[{"inset-be":H()}],top:[{top:H()}],right:[{right:H()}],bottom:[{bottom:H()}],left:[{left:H()}],visibility:["visible","invisible","collapse"],z:[{z:[ea,"auto",se,ne]}],basis:[{basis:[Zn,"full","auto",l,...x()]}],"flex-direction":[{flex:["row","row-reverse","col","col-reverse"]}],"flex-wrap":[{flex:["nowrap","wrap","wrap-reverse"]}],flex:[{flex:[je,Zn,"auto","initial","none",ne]}],grow:[{grow:["",je,se,ne]}],shrink:[{shrink:["",je,se,ne]}],order:[{order:[ea,"first","last","none",se,ne]}],"grid-cols":[{"grid-cols":te()}],"col-start-end":[{col:K()}],"col-start":[{"col-start":T()}],"col-end":[{"col-end":T()}],"grid-rows":[{"grid-rows":te()}],"row-start-end":[{row:K()}],"row-start":[{"row-start":T()}],"row-end":[{"row-end":T()}],"grid-flow":[{"grid-flow":["row","col","dense","row-dense","col-dense"]}],"auto-cols":[{"auto-cols":ie()}],"auto-rows":[{"auto-rows":ie()}],gap:[{gap:x()}],"gap-x":[{"gap-x":x()}],"gap-y":[{"gap-y":x()}],"justify-content":[{justify:[...fe(),"normal"]}],"justify-items":[{"justify-items":[...be(),"normal"]}],"justify-self":[{"justify-self":["auto",...be()]}],"align-content":[{content:["normal",...fe()]}],"align-items":[{items:[...be(),{baseline:["","last"]}]}],"align-self":[{self:["auto",...be(),{baseline:["","last"]}]}],"place-content":[{"place-content":fe()}],"place-items":[{"place-items":[...be(),"baseline"]}],"place-self":[{"place-self":["auto",...be()]}],p:[{p:x()}],px:[{px:x()}],py:[{py:x()}],ps:[{ps:x()}],pe:[{pe:x()}],pbs:[{pbs:x()}],pbe:[{pbe:x()}],pt:[{pt:x()}],pr:[{pr:x()}],pb:[{pb:x()}],pl:[{pl:x()}],m:[{m:ve()}],mx:[{mx:ve()}],my:[{my:ve()}],ms:[{ms:ve()}],me:[{me:ve()}],mbs:[{mbs:ve()}],mbe:[{mbe:ve()}],mt:[{mt:ve()}],mr:[{mr:ve()}],mb:[{mb:ve()}],ml:[{ml:ve()}],"space-x":[{"space-x":x()}],"space-x-reverse":["space-x-reverse"],"space-y":[{"space-y":x()}],"space-y-reverse":["space-y-reverse"],size:[{size:Ae()}],"inline-size":[{inline:["auto",...me()]}],"min-inline-size":[{"min-inline":["auto",...me()]}],"max-inline-size":[{"max-inline":["none",...me()]}],"block-size":[{block:["auto",...he()]}],"min-block-size":[{"min-block":["auto",...he()]}],"max-block-size":[{"max-block":["none",...he()]}],w:[{w:[l,"screen",...Ae()]}],"min-w":[{"min-w":[l,"screen","none",...Ae()]}],"max-w":[{"max-w":[l,"screen","none","prose",{screen:[i]},...Ae()]}],h:[{h:["screen","lh",...Ae()]}],"min-h":[{"min-h":["screen","lh","none",...Ae()]}],"max-h":[{"max-h":["screen","lh",...Ae()]}],"font-size":[{text:["base",r,fs,ha]}],"font-smoothing":["antialiased","subpixel-antialiased"],"font-style":["italic","not-italic"],"font-weight":[{font:[a,Nf,Ef]}],"font-stretch":[{"font-stretch":["ultra-condensed","extra-condensed","condensed","semi-condensed","normal","semi-expanded","expanded","extra-expanded","ultra-expanded",co,ne]}],"font-family":[{font:[Tf,Af,t]}],"font-features":[{"font-features":[ne]}],"fvn-normal":["normal-nums"],"fvn-ordinal":["ordinal"],"fvn-slashed-zero":["slashed-zero"],"fvn-figure":["lining-nums","oldstyle-nums"],"fvn-spacing":["proportional-nums","tabular-nums"],"fvn-fraction":["diagonal-fractions","stacked-fractions"],tracking:[{tracking:[s,se,ne]}],"line-clamp":[{"line-clamp":[je,"none",se,Ai]}],leading:[{leading:[o,...x()]}],"list-image":[{"list-image":["none",se,ne]}],"list-style-position":[{list:["inside","outside"]}],"list-style-type":[{list:["disc","decimal","none",se,ne]}],"text-alignment":[{text:["left","center","right","justify","start","end"]}],"placeholder-color":[{placeholder:W()}],"text-color":[{text:W()}],"text-decoration":["underline","overline","line-through","no-underline"],"text-decoration-style":[{decoration:[...ge(),"wavy"]}],"text-decoration-thickness":[{decoration:[je,"from-font","auto",se,ha]}],"text-decoration-color":[{decoration:W()}],"underline-offset":[{"underline-offset":[je,"auto",se,ne]}],"text-transform":["uppercase","lowercase","capitalize","normal-case"],"text-overflow":["truncate","text-ellipsis","text-clip"],"text-wrap":[{text:["wrap","nowrap","balance","pretty"]}],indent:[{indent:x()}],"vertical-align":[{align:["baseline","top","middle","bottom","text-top","text-bottom","sub","super",se,ne]}],whitespace:[{whitespace:["normal","nowrap","pre","pre-line","pre-wrap","break-spaces"]}],break:[{break:["normal","words","all","keep"]}],wrap:[{wrap:["break-word","anywhere","normal"]}],hyphens:[{hyphens:["none","manual","auto"]}],content:[{content:["none",se,ne]}],"bg-attachment":[{bg:["fixed","local","scroll"]}],"bg-clip":[{"bg-clip":["border","padding","content","text"]}],"bg-origin":[{"bg-origin":["border","padding","content"]}],"bg-position":[{bg:tt()}],"bg-repeat":[{bg:ke()}],"bg-size":[{bg:A()}],"bg-image":[{bg:["none",{linear:[{to:["t","tr","r","br","b","bl","l","tl"]},ea,se,ne],radial:["",se,ne],conic:[ea,se,ne]},Pf,zf]}],"bg-color":[{bg:W()}],"gradient-from-pos":[{from:re()}],"gradient-via-pos":[{via:re()}],"gradient-to-pos":[{to:re()}],"gradient-from":[{from:W()}],"gradient-via":[{via:W()}],"gradient-to":[{to:W()}],rounded:[{rounded:Y()}],"rounded-s":[{"rounded-s":Y()}],"rounded-e":[{"rounded-e":Y()}],"rounded-t":[{"rounded-t":Y()}],"rounded-r":[{"rounded-r":Y()}],"rounded-b":[{"rounded-b":Y()}],"rounded-l":[{"rounded-l":Y()}],"rounded-ss":[{"rounded-ss":Y()}],"rounded-se":[{"rounded-se":Y()}],"rounded-ee":[{"rounded-ee":Y()}],"rounded-es":[{"rounded-es":Y()}],"rounded-tl":[{"rounded-tl":Y()}],"rounded-tr":[{"rounded-tr":Y()}],"rounded-br":[{"rounded-br":Y()}],"rounded-bl":[{"rounded-bl":Y()}],"border-w":[{border:X()}],"border-w-x":[{"border-x":X()}],"border-w-y":[{"border-y":X()}],"border-w-s":[{"border-s":X()}],"border-w-e":[{"border-e":X()}],"border-w-bs":[{"border-bs":X()}],"border-w-be":[{"border-be":X()}],"border-w-t":[{"border-t":X()}],"border-w-r":[{"border-r":X()}],"border-w-b":[{"border-b":X()}],"border-w-l":[{"border-l":X()}],"divide-x":[{"divide-x":X()}],"divide-x-reverse":["divide-x-reverse"],"divide-y":[{"divide-y":X()}],"divide-y-reverse":["divide-y-reverse"],"border-style":[{border:[...ge(),"hidden","none"]}],"divide-style":[{divide:[...ge(),"hidden","none"]}],"border-color":[{border:W()}],"border-color-x":[{"border-x":W()}],"border-color-y":[{"border-y":W()}],"border-color-s":[{"border-s":W()}],"border-color-e":[{"border-e":W()}],"border-color-bs":[{"border-bs":W()}],"border-color-be":[{"border-be":W()}],"border-color-t":[{"border-t":W()}],"border-color-r":[{"border-r":W()}],"border-color-b":[{"border-b":W()}],"border-color-l":[{"border-l":W()}],"divide-color":[{divide:W()}],"outline-style":[{outline:[...ge(),"none","hidden"]}],"outline-offset":[{"outline-offset":[je,se,ne]}],"outline-w":[{outline:["",je,fs,ha]}],"outline-color":[{outline:W()}],shadow:[{shadow:["","none",p,Rs,Os]}],"shadow-color":[{shadow:W()}],"inset-shadow":[{"inset-shadow":["none",b,Rs,Os]}],"inset-shadow-color":[{"inset-shadow":W()}],"ring-w":[{ring:X()}],"ring-w-inset":["ring-inset"],"ring-color":[{ring:W()}],"ring-offset-w":[{"ring-offset":[je,ha]}],"ring-offset-color":[{"ring-offset":W()}],"inset-ring-w":[{"inset-ring":X()}],"inset-ring-color":[{"inset-ring":W()}],"text-shadow":[{"text-shadow":["none",_,Rs,Os]}],"text-shadow-color":[{"text-shadow":W()}],opacity:[{opacity:[je,se,ne]}],"mix-blend":[{"mix-blend":[...Z(),"plus-darker","plus-lighter"]}],"bg-blend":[{"bg-blend":Z()}],"mask-clip":[{"mask-clip":["border","padding","content","fill","stroke","view"]},"mask-no-clip"],"mask-composite":[{mask:["add","subtract","intersect","exclude"]}],"mask-image-linear-pos":[{"mask-linear":[je]}],"mask-image-linear-from-pos":[{"mask-linear-from":oe()}],"mask-image-linear-to-pos":[{"mask-linear-to":oe()}],"mask-image-linear-from-color":[{"mask-linear-from":W()}],"mask-image-linear-to-color":[{"mask-linear-to":W()}],"mask-image-t-from-pos":[{"mask-t-from":oe()}],"mask-image-t-to-pos":[{"mask-t-to":oe()}],"mask-image-t-from-color":[{"mask-t-from":W()}],"mask-image-t-to-color":[{"mask-t-to":W()}],"mask-image-r-from-pos":[{"mask-r-from":oe()}],"mask-image-r-to-pos":[{"mask-r-to":oe()}],"mask-image-r-from-color":[{"mask-r-from":W()}],"mask-image-r-to-color":[{"mask-r-to":W()}],"mask-image-b-from-pos":[{"mask-b-from":oe()}],"mask-image-b-to-pos":[{"mask-b-to":oe()}],"mask-image-b-from-color":[{"mask-b-from":W()}],"mask-image-b-to-color":[{"mask-b-to":W()}],"mask-image-l-from-pos":[{"mask-l-from":oe()}],"mask-image-l-to-pos":[{"mask-l-to":oe()}],"mask-image-l-from-color":[{"mask-l-from":W()}],"mask-image-l-to-color":[{"mask-l-to":W()}],"mask-image-x-from-pos":[{"mask-x-from":oe()}],"mask-image-x-to-pos":[{"mask-x-to":oe()}],"mask-image-x-from-color":[{"mask-x-from":W()}],"mask-image-x-to-color":[{"mask-x-to":W()}],"mask-image-y-from-pos":[{"mask-y-from":oe()}],"mask-image-y-to-pos":[{"mask-y-to":oe()}],"mask-image-y-from-color":[{"mask-y-from":W()}],"mask-image-y-to-color":[{"mask-y-to":W()}],"mask-image-radial":[{"mask-radial":[se,ne]}],"mask-image-radial-from-pos":[{"mask-radial-from":oe()}],"mask-image-radial-to-pos":[{"mask-radial-to":oe()}],"mask-image-radial-from-color":[{"mask-radial-from":W()}],"mask-image-radial-to-color":[{"mask-radial-to":W()}],"mask-image-radial-shape":[{"mask-radial":["circle","ellipse"]}],"mask-image-radial-size":[{"mask-radial":[{closest:["side","corner"],farthest:["side","corner"]}]}],"mask-image-radial-pos":[{"mask-radial-at":S()}],"mask-image-conic-pos":[{"mask-conic":[je]}],"mask-image-conic-from-pos":[{"mask-conic-from":oe()}],"mask-image-conic-to-pos":[{"mask-conic-to":oe()}],"mask-image-conic-from-color":[{"mask-conic-from":W()}],"mask-image-conic-to-color":[{"mask-conic-to":W()}],"mask-mode":[{mask:["alpha","luminance","match"]}],"mask-origin":[{"mask-origin":["border","padding","content","fill","stroke","view"]}],"mask-position":[{mask:tt()}],"mask-repeat":[{mask:ke()}],"mask-size":[{mask:A()}],"mask-type":[{"mask-type":["alpha","luminance"]}],"mask-image":[{mask:["none",se,ne]}],filter:[{filter:["","none",se,ne]}],blur:[{blur:ct()}],brightness:[{brightness:[je,se,ne]}],contrast:[{contrast:[je,se,ne]}],"drop-shadow":[{"drop-shadow":["","none",z,Rs,Os]}],"drop-shadow-color":[{"drop-shadow":W()}],grayscale:[{grayscale:["",je,se,ne]}],"hue-rotate":[{"hue-rotate":[je,se,ne]}],invert:[{invert:["",je,se,ne]}],saturate:[{saturate:[je,se,ne]}],sepia:[{sepia:["",je,se,ne]}],"backdrop-filter":[{"backdrop-filter":["","none",se,ne]}],"backdrop-blur":[{"backdrop-blur":ct()}],"backdrop-brightness":[{"backdrop-brightness":[je,se,ne]}],"backdrop-contrast":[{"backdrop-contrast":[je,se,ne]}],"backdrop-grayscale":[{"backdrop-grayscale":["",je,se,ne]}],"backdrop-hue-rotate":[{"backdrop-hue-rotate":[je,se,ne]}],"backdrop-invert":[{"backdrop-invert":["",je,se,ne]}],"backdrop-opacity":[{"backdrop-opacity":[je,se,ne]}],"backdrop-saturate":[{"backdrop-saturate":[je,se,ne]}],"backdrop-sepia":[{"backdrop-sepia":["",je,se,ne]}],"border-collapse":[{border:["collapse","separate"]}],"border-spacing":[{"border-spacing":x()}],"border-spacing-x":[{"border-spacing-x":x()}],"border-spacing-y":[{"border-spacing-y":x()}],"table-layout":[{table:["auto","fixed"]}],caption:[{caption:["top","bottom"]}],transition:[{transition:["","all","colors","opacity","shadow","transform","none",se,ne]}],"transition-behavior":[{transition:["normal","discrete"]}],duration:[{duration:[je,"initial",se,ne]}],ease:[{ease:["linear","initial",C,se,ne]}],delay:[{delay:[je,se,ne]}],animate:[{animate:["none",L,se,ne]}],backface:[{backface:["hidden","visible"]}],perspective:[{perspective:[I,se,ne]}],"perspective-origin":[{"perspective-origin":q()}],rotate:[{rotate:Bt()}],"rotate-x":[{"rotate-x":Bt()}],"rotate-y":[{"rotate-y":Bt()}],"rotate-z":[{"rotate-z":Bt()}],scale:[{scale:Rt()}],"scale-x":[{"scale-x":Rt()}],"scale-y":[{"scale-y":Rt()}],"scale-z":[{"scale-z":Rt()}],"scale-3d":["scale-3d"],skew:[{skew:wt()}],"skew-x":[{"skew-x":wt()}],"skew-y":[{"skew-y":wt()}],transform:[{transform:[se,ne,"","none","gpu","cpu"]}],"transform-origin":[{origin:q()}],"transform-style":[{transform:["3d","flat"]}],translate:[{translate:er()}],"translate-x":[{"translate-x":er()}],"translate-y":[{"translate-y":er()}],"translate-z":[{"translate-z":er()}],"translate-none":["translate-none"],accent:[{accent:W()}],appearance:[{appearance:["none","auto"]}],"caret-color":[{caret:W()}],"color-scheme":[{scheme:["normal","dark","light","light-dark","only-dark","only-light"]}],cursor:[{cursor:["auto","default","pointer","wait","text","move","help","not-allowed","none","context-menu","progress","cell","crosshair","vertical-text","alias","copy","no-drop","grab","grabbing","all-scroll","col-resize","row-resize","n-resize","e-resize","s-resize","w-resize","ne-resize","nw-resize","se-resize","sw-resize","ew-resize","ns-resize","nesw-resize","nwse-resize","zoom-in","zoom-out",se,ne]}],"field-sizing":[{"field-sizing":["fixed","content"]}],"pointer-events":[{"pointer-events":["auto","none"]}],resize:[{resize:["none","","y","x"]}],"scroll-behavior":[{scroll:["auto","smooth"]}],"scroll-m":[{"scroll-m":x()}],"scroll-mx":[{"scroll-mx":x()}],"scroll-my":[{"scroll-my":x()}],"scroll-ms":[{"scroll-ms":x()}],"scroll-me":[{"scroll-me":x()}],"scroll-mbs":[{"scroll-mbs":x()}],"scroll-mbe":[{"scroll-mbe":x()}],"scroll-mt":[{"scroll-mt":x()}],"scroll-mr":[{"scroll-mr":x()}],"scroll-mb":[{"scroll-mb":x()}],"scroll-ml":[{"scroll-ml":x()}],"scroll-p":[{"scroll-p":x()}],"scroll-px":[{"scroll-px":x()}],"scroll-py":[{"scroll-py":x()}],"scroll-ps":[{"scroll-ps":x()}],"scroll-pe":[{"scroll-pe":x()}],"scroll-pbs":[{"scroll-pbs":x()}],"scroll-pbe":[{"scroll-pbe":x()}],"scroll-pt":[{"scroll-pt":x()}],"scroll-pr":[{"scroll-pr":x()}],"scroll-pb":[{"scroll-pb":x()}],"scroll-pl":[{"scroll-pl":x()}],"snap-align":[{snap:["start","end","center","align-none"]}],"snap-stop":[{snap:["normal","always"]}],"snap-type":[{snap:["none","x","y","both"]}],"snap-strictness":[{snap:["mandatory","proximity"]}],touch:[{touch:["auto","none","manipulation"]}],"touch-x":[{"touch-pan":["x","left","right"]}],"touch-y":[{"touch-pan":["y","up","down"]}],"touch-pz":["touch-pinch-zoom"],select:[{select:["none","text","all","auto"]}],"will-change":[{"will-change":["auto","scroll","contents","transform",se,ne]}],fill:[{fill:["none",...W()]}],"stroke-w":[{stroke:[je,fs,ha,Ai]}],stroke:[{stroke:["none",...W()]}],"forced-color-adjust":[{"forced-color-adjust":["auto","none"]}]},conflictingClassGroups:{overflow:["overflow-x","overflow-y"],overscroll:["overscroll-x","overscroll-y"],inset:["inset-x","inset-y","inset-bs","inset-be","start","end","top","right","bottom","left"],"inset-x":["right","left"],"inset-y":["top","bottom"],flex:["basis","grow","shrink"],gap:["gap-x","gap-y"],p:["px","py","ps","pe","pbs","pbe","pt","pr","pb","pl"],px:["pr","pl"],py:["pt","pb"],m:["mx","my","ms","me","mbs","mbe","mt","mr","mb","ml"],mx:["mr","ml"],my:["mt","mb"],size:["w","h"],"font-size":["leading"],"fvn-normal":["fvn-ordinal","fvn-slashed-zero","fvn-figure","fvn-spacing","fvn-fraction"],"fvn-ordinal":["fvn-normal"],"fvn-slashed-zero":["fvn-normal"],"fvn-figure":["fvn-normal"],"fvn-spacing":["fvn-normal"],"fvn-fraction":["fvn-normal"],"line-clamp":["display","overflow"],rounded:["rounded-s","rounded-e","rounded-t","rounded-r","rounded-b","rounded-l","rounded-ss","rounded-se","rounded-ee","rounded-es","rounded-tl","rounded-tr","rounded-br","rounded-bl"],"rounded-s":["rounded-ss","rounded-es"],"rounded-e":["rounded-se","rounded-ee"],"rounded-t":["rounded-tl","rounded-tr"],"rounded-r":["rounded-tr","rounded-br"],"rounded-b":["rounded-br","rounded-bl"],"rounded-l":["rounded-tl","rounded-bl"],"border-spacing":["border-spacing-x","border-spacing-y"],"border-w":["border-w-x","border-w-y","border-w-s","border-w-e","border-w-bs","border-w-be","border-w-t","border-w-r","border-w-b","border-w-l"],"border-w-x":["border-w-r","border-w-l"],"border-w-y":["border-w-t","border-w-b"],"border-color":["border-color-x","border-color-y","border-color-s","border-color-e","border-color-bs","border-color-be","border-color-t","border-color-r","border-color-b","border-color-l"],"border-color-x":["border-color-r","border-color-l"],"border-color-y":["border-color-t","border-color-b"],translate:["translate-x","translate-y","translate-none"],"translate-none":["translate","translate-x","translate-y","translate-z"],"scroll-m":["scroll-mx","scroll-my","scroll-ms","scroll-me","scroll-mbs","scroll-mbe","scroll-mt","scroll-mr","scroll-mb","scroll-ml"],"scroll-mx":["scroll-mr","scroll-ml"],"scroll-my":["scroll-mt","scroll-mb"],"scroll-p":["scroll-px","scroll-py","scroll-ps","scroll-pe","scroll-pbs","scroll-pbe","scroll-pt","scroll-pr","scroll-pb","scroll-pl"],"scroll-px":["scroll-pr","scroll-pl"],"scroll-py":["scroll-pt","scroll-pb"],touch:["touch-x","touch-y","touch-pz"],"touch-x":["touch"],"touch-y":["touch"],"touch-pz":["touch"]},conflictingClassGroupModifiers:{"font-size":["leading"]},orderSensitiveModifiers:["*","**","after","backdrop","before","details-content","file","first-letter","first-line","marker","placeholder","selection"]}},Of=pf(Lf);function Nt(...e){return Of(Dl(e))}const $o="dartlab-conversations",Ii=50;function Rf(){return Date.now().toString(36)+Math.random().toString(36).slice(2,8)}function Df(){try{const e=localStorage.getItem($o);return e?JSON.parse(e):{conversations:[],activeId:null}}catch{return{conversations:[],activeId:null}}}const jf=["systemPrompt","userContent","contexts","snapshot","toolEvents","startedAt","loading"];function Pi(e){return e.map(t=>({...t,messages:t.messages.map(r=>{if(r.role!=="assistant")return r;const a={};for(const[s,o]of Object.entries(r))jf.includes(s)||(a[s]=o);return a})}))}function Ni(e){try{const t={conversations:Pi(e.conversations),activeId:e.activeId};localStorage.setItem($o,JSON.stringify(t))}catch{if(e.conversations.length>5){e.conversations=e.conversations.slice(0,e.conversations.length-5);try{const t={conversations:Pi(e.conversations),activeId:e.activeId};localStorage.setItem($o,JSON.stringify(t))}catch{}}}}function Vf(){const e=Df(),t=e.conversations||[],r=t.find(C=>C.id===e.activeId)?e.activeId:null;let a=G(qt(t)),s=G(qt(r)),o=null;function i(){o&&clearTimeout(o),o=setTimeout(()=>{Ni({conversations:n(a),activeId:n(s)}),o=null},300)}function l(){o&&clearTimeout(o),o=null,Ni({conversations:n(a),activeId:n(s)})}function c(){return n(a).find(C=>C.id===n(s))||null}function f(){const C={id:Rf(),title:"새 대화",messages:[],createdAt:Date.now(),updatedAt:Date.now()};return u(a,[C,...n(a)],!0),n(a).length>Ii&&u(a,n(a).slice(0,Ii),!0),u(s,C.id,!0),l(),C.id}function p(C){n(a).find(L=>L.id===C)&&(u(s,C,!0),l())}function b(C,L,U=null){const S=c();if(!S)return;const q={role:C,text:L};U&&(q.meta=U),S.messages=[...S.messages,q],S.updatedAt=Date.now(),S.title==="새 대화"&&C==="user"&&(S.title=L.length>30?L.slice(0,30)+"...":L),u(a,[...n(a)],!0),l()}function _(C){const L=c();if(!L||L.messages.length===0)return;const U=L.messages[L.messages.length-1];Object.assign(U,C),L.updatedAt=Date.now(),u(a,[...n(a)],!0),i()}function z(C){u(a,n(a).filter(L=>L.id!==C),!0),n(s)===C&&u(s,n(a).length>0?n(a)[0].id:null,!0),l()}function y(){const C=c();!C||C.messages.length===0||(C.messages=C.messages.slice(0,-1),C.updatedAt=Date.now(),u(a,[...n(a)],!0),l())}function I(C,L){const U=n(a).find(S=>S.id===C);U&&(U.title=L,u(a,[...n(a)],!0),l())}function k(){u(a,[],!0),u(s,null),l()}return{get conversations(){return n(a)},get activeId(){return n(s)},get active(){return c()},createConversation:f,setActive:p,addMessage:b,updateLastMessage:_,removeLastMessage:y,deleteConversation:z,updateTitle:I,clearAll:k,flush:l}}const ad="dartlab-workspace",qf=6;function sd(){return typeof window<"u"&&typeof localStorage<"u"}function Ff(){if(!sd())return{};try{const e=localStorage.getItem(ad);return e?JSON.parse(e):{}}catch{return{}}}function Bf(e){sd()&&localStorage.setItem(ad,JSON.stringify(e))}function Gf(){const e=Ff();let t=G(!1),r=G(null),a=G(null),s=G("explore"),o=G(null),i=G(null),l=G(null),c=G(null),f=G(qt(e.selectedCompany||null)),p=G(qt(e.recentCompanies||[]));function b(){Bf({selectedCompany:n(f),recentCompanies:n(p)})}function _($){if(!($!=null&&$.stockCode))return;const x={stockCode:$.stockCode,corpName:$.corpName||$.company||$.stockCode,company:$.company||$.corpName||$.stockCode,market:$.market||""};u(p,[x,...n(p).filter(H=>H.stockCode!==x.stockCode)].slice(0,qf),!0)}function z($){$&&(u(f,$,!0),_($)),u(r,"viewer"),u(a,null),u(t,!0),b()}function y($){u(r,"data"),u(a,$,!0),u(t,!0),q("explore")}function I(){u(t,!1)}function k($){u(f,$,!0),$&&_($),b()}function C($,x){var H,te,K,T;!($!=null&&$.company)&&!($!=null&&$.stockCode)||(u(f,{...n(f)||{},...x||{},corpName:$.company||((H=n(f))==null?void 0:H.corpName)||(x==null?void 0:x.corpName)||(x==null?void 0:x.company),company:$.company||((te=n(f))==null?void 0:te.company)||(x==null?void 0:x.company)||(x==null?void 0:x.corpName),stockCode:$.stockCode||((K=n(f))==null?void 0:K.stockCode)||(x==null?void 0:x.stockCode),market:((T=n(f))==null?void 0:T.market)||(x==null?void 0:x.market)||""},!0),_(n(f)),b())}function L($,x){u(l,$,!0),u(c,x||$,!0)}function U($,x=null){u(r,"data"),u(t,!0),u(s,"evidence"),u(o,$,!0),u(i,Number.isInteger(x)?x:null,!0)}function S(){u(o,null),u(i,null)}function q($){u(s,$||"explore",!0),n(s)!=="evidence"&&S()}function le(){return n(t)?n(r)==="viewer"&&n(f)?{type:"viewer",company:n(f),topic:n(l),topicLabel:n(c)}:n(r)==="data"&&n(a)?{type:"data",data:n(a)}:null:null}return{get panelOpen(){return n(t)},get panelMode(){return n(r)},get panelData(){return n(a)},get activeTab(){return n(s)},get activeEvidenceSection(){return n(o)},get selectedEvidenceIndex(){return n(i)},get selectedCompany(){return n(f)},get recentCompanies(){return n(p)},get viewerTopic(){return n(l)},get viewerTopicLabel(){return n(c)},openViewer:z,openData:y,openEvidence:U,closePanel:I,selectCompany:k,setViewerTopic:L,clearEvidenceSelection:S,setTab:q,syncCompanyFromMessage:C,getViewContext:le}}var Hf=h("<a><!></a>"),Uf=h("<button><!></button>");function Wf(e,t){rn(t,!0);let r=dt(t,"variant",3,"default"),a=dt(t,"size",3,"default"),s=$u(t,["$$slots","$$events","$$legacy","variant","size","class","children"]);const o={default:"bg-gradient-to-r from-dl-primary to-dl-primary-dark text-white shadow-lg shadow-dl-primary/25 hover:shadow-dl-primary/40 hover:-translate-y-0.5",secondary:"bg-dl-bg-card border border-dl-border text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover",ghost:"text-dl-text-muted hover:text-dl-text hover:bg-white/5",outline:"border border-dl-border text-dl-text-muted hover:text-dl-text hover:border-dl-primary/50"},i={default:"px-5 py-2 text-sm",sm:"px-3 py-1.5 text-xs",lg:"px-7 py-3 text-base",icon:"w-9 h-9"};var l=ye(),c=ee(l);{var f=b=>{var _=Hf();qs(_,y=>({class:y,...s}),[()=>Nt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer no-underline",o[r()],i[a()],t.class)]);var z=d(_);To(z,()=>t.children),v(b,_)},p=b=>{var _=Uf();qs(_,y=>({class:y,...s}),[()=>Nt("inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 cursor-pointer",o[r()],i[a()],t.class)]);var z=d(_);To(z,()=>t.children),v(b,_)};E(c,b=>{t.href?b(f):b(p,-1)})}v(e,l),nn()}Cc();/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Kf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Yf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The MIT License (MIT) (for portions derived from Feather)
 * 
 * Copyright (c) 2013-2026 Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const $i=(...e)=>e.filter((t,r,a)=>!!t&&t.trim()!==""&&a.indexOf(t)===r).join(" ").trim();var Xf=pu("<svg><!><!></svg>");function Xe(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]),a=Ve(r,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);rn(t,!1);let s=dt(t,"name",8,void 0),o=dt(t,"color",8,"currentColor"),i=dt(t,"size",8,24),l=dt(t,"strokeWidth",8,2),c=dt(t,"absoluteStrokeWidth",8,!1),f=dt(t,"iconNode",24,()=>[]);Iu();var p=Xf();qs(p,(z,y,I)=>({...Kf,...z,...a,width:i(),height:i(),stroke:o(),"stroke-width":y,class:I}),[()=>Yf(a)?void 0:{"aria-hidden":"true"},()=>(ga(c()),ga(l()),ga(i()),Ia(()=>c()?Number(l())*24/Number(i()):l())),()=>(ga($i),ga(s()),ga(r),Ia(()=>$i("lucide-icon","lucide",s()?`lucide-${s()}`:"",r.class)))]);var b=d(p);Ie(b,1,f,Te,(z,y)=>{var I=B(()=>Ui(n(y),2));let k=()=>n(I)[0],C=()=>n(I)[1];var L=ye(),U=ee(L);yu(U,k,!0,(S,q)=>{qs(S,()=>({...C()}))}),v(z,L)});var _=m(b);Ue(_,t,"default",{}),v(e,p),nn()}function Jf(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];Xe(e,Ye({name:"activity"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Qf(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m5 12 7-7 7 7"}],["path",{d:"M12 19V5"}]];Xe(e,Ye({name:"arrow-up"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Li(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 7v14"}],["path",{d:"M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"}]];Xe(e,Ye({name:"book-open"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function uo(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 18V5"}],["path",{d:"M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"}],["path",{d:"M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"}],["path",{d:"M17.997 5.125a4 4 0 0 1 2.526 5.77"}],["path",{d:"M18 18a4 4 0 0 0 2-7.464"}],["path",{d:"M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"}],["path",{d:"M6 18a4 4 0 0 1-2-7.464"}],["path",{d:"M6.003 5.125a4 4 0 0 0-2.526 5.77"}]];Xe(e,Ye({name:"brain"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Zf(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M18 17V9"}],["path",{d:"M13 17V5"}],["path",{d:"M8 17v-3"}]];Xe(e,Ye({name:"chart-column"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ev(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M20 6 9 17l-5-5"}]];Xe(e,Ye({name:"check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function tv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m6 9 6 6 6-6"}]];Xe(e,Ye({name:"chevron-down"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function rv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m9 18 6-6-6-6"}]];Xe(e,Ye({name:"chevron-right"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function vs(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["line",{x1:"12",x2:"12",y1:"8",y2:"12"}],["line",{x1:"12",x2:"12.01",y1:"16",y2:"16"}]];Xe(e,Ye({name:"circle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function _s(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"m9 12 2 2 4-4"}]];Xe(e,Ye({name:"circle-check"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function nv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M12 6v6l4 2"}]];Xe(e,Ye({name:"clock"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function av(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 18 6-6-6-6"}],["path",{d:"m8 6-6 6 6 6"}]];Xe(e,Ye({name:"code"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function sv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 2v2"}],["path",{d:"M14 2v2"}],["path",{d:"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1"}],["path",{d:"M6 2v2"}]];Xe(e,Ye({name:"coffee"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ps(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["ellipse",{cx:"12",cy:"5",rx:"9",ry:"3"}],["path",{d:"M3 5V19A9 3 0 0 0 21 19V5"}],["path",{d:"M3 12A9 3 0 0 0 21 12"}]];Xe(e,Ye({name:"database"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ws(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 15V3"}],["path",{d:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{d:"m7 10 5 5 5-5"}]];Xe(e,Ye({name:"download"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Oi(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"M10 14 21 3"}],["path",{d:"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"}]];Xe(e,Ye({name:"external-link"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ov(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"}],["circle",{cx:"12",cy:"12",r:"3"}]];Xe(e,Ye({name:"eye"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function jn(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5"}],["path",{d:"M10 9H8"}],["path",{d:"M16 13H8"}],["path",{d:"M16 17H8"}]];Xe(e,Ye({name:"file-text"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function iv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"}],["path",{d:"M9 18c-4.51 2-5-2-7-2"}]];Xe(e,Ye({name:"github"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Ri(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"}],["path",{d:"m21 2-9.6 9.6"}],["circle",{cx:"7.5",cy:"15.5",r:"5.5"}]];Xe(e,Ye({name:"key"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function vn(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M21 12a9 9 0 1 1-6.219-8.56"}]];Xe(e,Ye({name:"loader-circle"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function lv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m16 17 5-5-5-5"}],["path",{d:"M21 12H9"}],["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"}]];Xe(e,Ye({name:"log-out"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function od(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M15 3h6v6"}],["path",{d:"m21 3-7 7"}],["path",{d:"m3 21 7-7"}],["path",{d:"M9 21H3v-6"}]];Xe(e,Ye({name:"maximize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function dv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M4 5h16"}],["path",{d:"M4 12h16"}],["path",{d:"M4 19h16"}]];Xe(e,Ye({name:"menu"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Di(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"}]];Xe(e,Ye({name:"message-square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function id(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m14 10 7-7"}],["path",{d:"M20 10h-6V4"}],["path",{d:"m3 21 7-7"}],["path",{d:"M4 14h6v6"}]];Xe(e,Ye({name:"minimize-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function cv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}],["path",{d:"M9 3v18"}],["path",{d:"m16 15-3-3 3-3"}]];Xe(e,Ye({name:"panel-left-close"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ji(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M5 12h14"}],["path",{d:"M12 5v14"}]];Xe(e,Ye({name:"plus"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function uv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Xe(e,Ye({name:"refresh-cw"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function ys(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21 21-4.34-4.34"}],["circle",{cx:"11",cy:"11",r:"8"}]];Xe(e,Ye({name:"search"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function fv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Xe(e,Ye({name:"settings"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function vv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2"}]];Xe(e,Ye({name:"square"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function pv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M12 19h8"}],["path",{d:"m4 17 6-6-6-6"}]];Xe(e,Ye({name:"terminal"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function mv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Xe(e,Ye({name:"trash-2"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function hv(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];Xe(e,Ye({name:"triangle-alert"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Vi(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"}]];Xe(e,Ye({name:"wrench"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}function Bs(e,t){const r=Ve(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v0.575.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2026 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2026.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The MIT License (MIT) (for portions derived from Feather)
 *
 * Copyright (c) 2013-2026 Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const a=[["path",{d:"M18 6 6 18"}],["path",{d:"m6 6 12 12"}]];Xe(e,Ye({name:"x"},()=>r,{get iconNode(){return a},children:(s,o)=>{var i=ye(),l=ee(i);Ue(l,t,"default",{}),v(s,i)},$$slots:{default:!0}}))}var gv=h("<!> 새 대화",1),xv=h('<div class="px-3 pb-2"><div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60"><!> <input type="text" placeholder="대화 검색..." class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"/></div></div>'),bv=h('<div><button class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"><!> <span class="flex-1 truncate"> </span></button> <button class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"><!></button></div>'),_v=h('<div><div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider"> </div> <!></div>'),wv=h('<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40"><span class="text-[10px] text-dl-text-dim font-mono"> </span></div>'),yv=h('<div class="flex flex-col h-full min-w-[260px]"><div class="border-b border-dl-border/40 px-4 pt-4 pb-3"><div class="flex items-center gap-2.5"><img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm"/> <div><div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div> <div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div></div></div></div> <div class="p-3 pb-2"><!></div> <!> <div class="flex-1 overflow-y-auto px-2 py-1 space-y-4"></div> <!></div>'),kv=h("<button><!></button>"),Cv=h('<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1"/> <button class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors" title="새 대화"><!></button> <div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1"></div></div>'),Sv=h("<aside><!></aside>");function Mv(e,t){rn(t,!0);let r=dt(t,"conversations",19,()=>[]),a=dt(t,"activeId",3,null),s=dt(t,"open",3,!0),o=dt(t,"version",3,""),i=G("");function l(y){const I=new Date().setHours(0,0,0,0),k=I-864e5,C=I-7*864e5,L={오늘:[],어제:[],"이번 주":[],이전:[]};for(const S of y)S.updatedAt>=I?L.오늘.push(S):S.updatedAt>=k?L.어제.push(S):S.updatedAt>=C?L["이번 주"].push(S):L.이전.push(S);const U=[];for(const[S,q]of Object.entries(L))q.length>0&&U.push({label:S,items:q});return U}let c=B(()=>n(i).trim()?r().filter(y=>y.title.toLowerCase().includes(n(i).toLowerCase())):r()),f=B(()=>l(n(c)));var p=Sv(),b=d(p);{var _=y=>{var I=yv(),k=m(d(I),2),C=d(k);Wf(C,{variant:"secondary",class:"w-full justify-start gap-2",get onclick(){return t.onNewChat},children:($,x)=>{var H=gv(),te=ee(H);ji(te,{size:16}),v($,H)},$$slots:{default:!0}});var L=m(k,2);{var U=$=>{var x=xv(),H=d(x),te=d(H);ys(te,{size:12,class:"text-dl-text-dim flex-shrink-0"});var K=m(te,2);ja(K,()=>n(i),T=>u(i,T)),v($,x)};E(L,$=>{r().length>3&&$(U)})}var S=m(L,2);Ie(S,21,()=>n(f),Te,($,x)=>{var H=_v(),te=d(H),K=d(te),T=m(te,2);Ie(T,17,()=>n(x).items,Te,(ie,fe)=>{var be=bv(),ve=d(be),Ae=d(ve);Di(Ae,{size:14,class:"flex-shrink-0 opacity-50"});var me=m(Ae,2),he=d(me),W=m(ve,2),tt=d(W);mv(tt,{size:12}),N(ke=>{Le(be,1,ke),qn(ve,"aria-current",n(fe).id===a()?"true":void 0),P(he,n(fe).title),qn(W,"aria-label",`${n(fe).title} 삭제`)},[()=>Pt(Nt("w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",n(fe).id===a()?"bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15":"text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"))]),ae("click",ve,()=>{var ke;return(ke=t.onSelect)==null?void 0:ke.call(t,n(fe).id)}),ae("click",W,ke=>{var A;ke.stopPropagation(),(A=t.onDelete)==null||A.call(t,n(fe).id)}),v(ie,be)}),N(()=>P(K,n(x).label)),v($,H)});var q=m(S,2);{var le=$=>{var x=wv(),H=d(x),te=d(H);N(()=>P(te,`v${o()??""}`)),v($,x)};E(q,$=>{o()&&$(le)})}v(y,I)},z=y=>{var I=Cv(),k=m(d(I),2),C=d(k);ji(C,{size:18});var L=m(k,2);Ie(L,21,()=>r().slice(0,10),Te,(U,S)=>{var q=kv(),le=d(q);Di(le,{size:16}),N($=>{Le(q,1,$),qn(q,"title",n(S).title)},[()=>Pt(Nt("p-2 rounded-lg transition-colors w-full flex justify-center",n(S).id===a()?"bg-dl-bg-card text-dl-text":"text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"))]),ae("click",q,()=>{var $;return($=t.onSelect)==null?void 0:$.call(t,n(S).id)}),v(U,q)}),ae("click",k,function(...U){var S;(S=t.onNewChat)==null||S.apply(this,U)}),v(y,I)};E(b,y=>{s()?y(_):y(z,-1)})}N(y=>Le(p,1,y),[()=>Pt(Nt("surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",s()?"w-[260px]":"w-[52px]"))]),v(e,p),nn()}Bn(["click"]);var Ev=h('<button class="send-btn active"><!></button>'),Av=h("<button><!></button>"),zv=h('<span class="text-[10px] text-dl-text-dim flex-shrink-0"> </span>'),Tv=h('<div><!> <div class="flex-1 min-w-0"><div class="text-[13px] font-medium truncate"> </div> <div class="text-[10px] text-dl-text-dim"> </div></div> <!></div>'),Iv=h('<div class="absolute left-0 right-0 bottom-full mb-1.5 z-20 bg-dl-bg-card border border-dl-border rounded-xl shadow-2xl shadow-black/40 overflow-hidden animate-fadeIn"></div>'),Pv=h('<div class="relative w-full"><div><textarea rows="1" class="input-textarea"></textarea> <!></div> <!></div>');function ld(e,t){rn(t,!0);let r=dt(t,"inputText",15,""),a=dt(t,"isLoading",3,!1),s=dt(t,"large",3,!1),o=dt(t,"placeholder",3,"메시지를 입력하세요..."),i=G(qt([])),l=G(!1),c=G(-1),f=null,p=G(void 0);function b(x){var H;if(n(l)&&n(i).length>0){if(x.key==="ArrowDown"){x.preventDefault(),u(c,(n(c)+1)%n(i).length);return}if(x.key==="ArrowUp"){x.preventDefault(),u(c,n(c)<=0?n(i).length-1:n(c)-1,!0);return}if(x.key==="Enter"&&n(c)>=0){x.preventDefault(),y(n(i)[n(c)]);return}if(x.key==="Escape"){u(l,!1),u(c,-1);return}}x.key==="Enter"&&!x.shiftKey&&(x.preventDefault(),u(l,!1),(H=t.onSend)==null||H.call(t))}function _(x){x.target.style.height="auto",x.target.style.height=Math.min(x.target.scrollHeight,200)+"px"}function z(x){_(x);const H=r();f&&clearTimeout(f),H.length>=2&&!/\s/.test(H.slice(-1))?f=setTimeout(async()=>{var te;try{const K=await Bl(H.trim());((te=K.results)==null?void 0:te.length)>0?(u(i,K.results.slice(0,6),!0),u(l,!0),u(c,-1)):u(l,!1)}catch{u(l,!1)}},300):u(l,!1)}function y(x){var H;r(`${x.corpName} `),u(l,!1),u(c,-1),(H=t.onCompanySelect)==null||H.call(t,x),n(p)&&n(p).focus()}function I(){setTimeout(()=>{u(l,!1)},200)}var k=Pv(),C=d(k),L=d(C);Aa(L,x=>u(p,x),()=>n(p));var U=m(L,2);{var S=x=>{var H=Ev(),te=d(H);vv(te,{size:14}),ae("click",H,function(...K){var T;(T=t.onStop)==null||T.apply(this,K)}),v(x,H)},q=x=>{var H=Av(),te=d(H);{let K=B(()=>s()?18:16);Qf(te,{get size(){return n(K)},strokeWidth:2.5})}N((K,T)=>{Le(H,1,K),H.disabled=T},[()=>Pt(Nt("send-btn",r().trim()&&"active")),()=>!r().trim()]),ae("click",H,()=>{var K;u(l,!1),(K=t.onSend)==null||K.call(t)}),v(x,H)};E(U,x=>{a()&&t.onStop?x(S):x(q,-1)})}var le=m(C,2);{var $=x=>{var H=Iv();Ie(H,21,()=>n(i),Te,(te,K,T)=>{var ie=Tv(),fe=d(ie);ys(fe,{size:13,class:"flex-shrink-0 text-dl-text-dim"});var be=m(fe,2),ve=d(be),Ae=d(ve),me=m(ve,2),he=d(me),W=m(be,2);{var tt=ke=>{var A=zv(),re=d(A);N(()=>P(re,n(K).sector)),v(ke,A)};E(W,ke=>{n(K).sector&&ke(tt)})}N(ke=>{Le(ie,1,ke),P(Ae,n(K).corpName),P(he,`${n(K).stockCode??""} · ${(n(K).market||"")??""}`)},[()=>Pt(Nt("flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",T===n(c)?"bg-dl-primary/10 text-dl-text":"text-dl-text-muted hover:bg-white/[0.03]"))]),ae("mousedown",ie,()=>y(n(K))),Va("mouseenter",ie,()=>{u(c,T,!0)}),v(te,ie)}),v(x,H)};E(le,x=>{n(l)&&n(i).length>0&&x($)})}N(x=>{Le(C,1,x),qn(L,"placeholder",o())},[()=>Pt(Nt("input-box",s()&&"large"))]),ae("keydown",L,b),ae("input",L,z),Va("blur",L,I),ja(L,r),v(e,k),nn()}Bn(["keydown","input","click","mousedown"]);var Nv=h('<button class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"> </button>'),$v=h(`<div class="flex-1 flex flex-col items-center justify-center px-5"><div class="w-full max-w-[580px] flex flex-col items-center"><div class="relative mb-8"><div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div> <img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full"/></div> <h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1> <p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p> <div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left"><div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div> <div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.</div></div> <div class="w-full"><!></div> <div class="mt-5 flex w-full flex-wrap justify-center gap-2"></div></div></div>`);function Lv(e,t){rn(t,!0);let r=dt(t,"inputText",15,"");const a=["지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘","EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘","OpenDart와 OpenEdgar로 가능한 일을 비교해줘","GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘"];var s=$v(),o=d(s),i=m(d(o),8),l=d(i);ld(l,{large:!0,placeholder:"삼성전자 재무 건전성을 분석해줘...",get onSend(){return t.onSend},get onCompanySelect(){return t.onCompanySelect},get inputText(){return r()},set inputText(f){r(f)}});var c=m(i,2);Ie(c,21,()=>a,Te,(f,p)=>{var b=Nv(),_=d(b);N(()=>P(_,n(p))),ae("click",b,()=>{var z;return(z=t.onSend)==null?void 0:z.call(t,n(p))}),v(f,b)}),v(e,s),nn()}Bn(["click"]);var Ov=h("<span><!></span>");function ms(e,t){rn(t,!0);let r=dt(t,"variant",3,"default");const a={default:"bg-dl-primary/10 text-dl-primary-light border-dl-primary/20",accent:"bg-dl-accent/10 text-dl-accent-light border-dl-accent/20",success:"bg-dl-success/10 text-dl-success border-dl-success/20",muted:"bg-dl-bg-card-hover text-dl-text-muted border-dl-border",dim:"bg-dl-bg-card/60 text-dl-text-dim border-dl-border/50"};var s=Ov(),o=d(s);To(o,()=>t.children),N(i=>Le(s,1,i),[()=>Pt(Nt("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",a[r()],t.class))]),v(e,s),nn()}function Rv(e){const t=e.replace(/<\/?strong>/g,"").replace(/\*\*/g,"").trim();return/^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(t)||t==="-"||t==="0"}function es(e){if(!e)return"";let t=[],r=[],a=e.replace(/```(\w*)\n([\s\S]*?)```/g,(o,i,l)=>{const c=t.length;return t.push(l.trimEnd()),`
%%CODE_${c}%%
`});a=a.replace(/((?:^\|.+\|$\n?)+)/gm,o=>{const i=o.trim().split(`
`).filter(_=>_.trim());let l=null,c=-1,f=[];for(let _=0;_<i.length;_++)if(i[_].slice(1,-1).split("|").map(y=>y.trim()).every(y=>/^[\-:]+$/.test(y))){c=_;break}c>0?(l=i[c-1],f=i.slice(c+1)):(c===0||(l=i[0]),f=i.slice(1));let p="<table>";if(l){const _=l.slice(1,-1).split("|").map(z=>z.trim());p+="<thead><tr>"+_.map(z=>`<th>${z.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>")}</th>`).join("")+"</tr></thead>"}if(f.length>0){p+="<tbody>";for(const _ of f){const z=_.slice(1,-1).split("|").map(y=>y.trim());p+="<tr>"+z.map(y=>{let I=y.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");return`<td${Rv(y)?' class="num"':""}>${I}</td>`}).join("")+"</tr>"}p+="</tbody>"}p+="</table>";let b=r.length;return r.push(p),`
%%TABLE_${b}%%
`});let s=a.replace(/`([^`]+)`/g,"<code>$1</code>").replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>").replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/^[•\-\*] (.+)$/gm,"<li>$1</li>").replace(/^\d+\. (.+)$/gm,"<li>$1</li>").replace(/^> (.+)$/gm,"<blockquote>$1</blockquote>").replace(/\n\n/g,"</p><p>").replace(/\n/g,"<br>");s=s.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g,o=>"<ul>"+o.replace(/<br>/g,"")+"</ul>");for(let o=0;o<r.length;o++)s=s.replace(`%%TABLE_${o}%%`,r[o]);for(let o=0;o<t.length;o++){const i=t[o].replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");s=s.replace(`%%CODE_${o}%%`,`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${o}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${i}</code></pre></div>`)}return s=s.replace(new RegExp("(?<=>|^)([^<]*?)(?=<|$)","g"),(o,i)=>i.replace(new RegExp("(?<![a-zA-Z가-힣/\\-])([−\\-+]?\\d[\\d,]*\\.?\\d*)(\\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)","g"),'<span class="num-highlight">$1$2$3</span>')),"<p>"+s+"</p>"}var Dv=h('<div class="flex items-start gap-3 animate-fadeIn"><div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">You</div> <div class="flex-1 pt-0.5"><p class="text-[15px] text-dl-text leading-relaxed"> </p></div></div>'),jv=h('<button class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"><!> </button>'),Vv=h('<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim"><!> </span>'),qv=h('<button class="inline-flex items-center gap-1 rounded-full border border-dl-border/50 bg-dl-bg-card/35 px-2 py-0.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"><!> </button>'),Fv=h('<div class="message-section-slot message-transparency-slot mb-3 rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim"><!> 투명성</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">이 응답을 만들 때 실제로 참조한 회사, 기간, 컨텍스트, 툴 활동을 바로 열어볼 수 있습니다.</div> <div class="flex flex-wrap items-center gap-1.5"><!> <!> <!> <!> <!> <!> <!></div></div>'),Bv=h('<div class="px-3 py-2 bg-dl-bg-card/50"><div class="text-[10px] text-dl-text-dim leading-tight"> </div> <div> </div></div>'),Gv=h('<span class="flex items-center gap-1 text-[10px] text-amber-400"><!> </span>'),Hv=h('<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2"></div>'),Uv=h('<button class="message-section-slot mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"><div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));"></div> <!></button>'),Wv=h("<button><!> </button>"),Kv=h('<div class="message-section-slot mb-3"><div class="rounded-2xl border border-dl-border/40 bg-dl-bg-card/20 p-3"><div class="mb-2 text-[10px] uppercase tracking-[0.18em] text-dl-text-dim">보고 있는 것 / 하고 있는 것</div> <div class="mb-2 text-[11px] leading-relaxed text-dl-text-dim">응답 중에 실제로 호출한 도구와 반환된 결과 흐름입니다. 배지를 누르면 상세 근거로 이동합니다.</div> <div class="flex flex-wrap items-center gap-1.5"></div></div></div>'),Yv=h('<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg></span> <span class="text-dl-text-muted"> </span>',1),Xv=h('<!> <span class="text-dl-text-dim"> </span>',1),Jv=h('<div class="flex items-center gap-2 text-[11px]"><!></div>'),Qv=h('<div class="animate-fadeIn"><div class="space-y-1 mb-3"></div> <div class="space-y-2.5"><div class="skeleton-line w-full"></div> <div class="skeleton-line w-[85%]"></div> <div class="skeleton-line w-[70%]"></div></div></div>'),Zv=h('<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim"><!> <span> </span></div>'),ep=h('<div class="message-committed"><!></div>'),tp=h('<div><div class="message-live-label"> </div> <pre> </pre></div>'),rp=h('<span class="flex items-center gap-1 text-[10px] text-dl-text-dim"><!> </span>'),np=h('<span class="text-dl-accent/60"> </span>'),ap=h('<span class="text-dl-success/60"> </span>'),sp=h('<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)"><!> <!></span>'),op=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 재생성</button>'),ip=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"><!> 시스템 프롬프트</button>'),lp=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"><!> </button>'),dp=h('<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20"><!> <!> <!> <!> <!></div>'),cp=h("<!>  <div><!> <!></div> <!>",1),up=h('<div class="flex items-start gap-3 animate-fadeIn"><img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5"/> <div class="message-shell flex-1 pt-0.5 min-w-0"><!> <!> <!> <!></div></div>'),fp=h('<span class="text-[10px] text-dl-text-dim"> </span>'),vp=h('<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5"><button><!> 렌더링</button> <button><!> 원문</button></div>'),pp=h("<button> </button>"),mp=h('<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide"><div class="flex items-center gap-1.5"></div></div>'),hp=h("<button>시스템 프롬프트</button>"),gp=h("<button>LLM 입력</button>"),xp=h('<div class="px-5 pb-2.5"><div class="flex items-center gap-1.5"><!> <!></div></div>'),bp=h('<div class="prose-dartlab text-[13px] leading-[1.7] pt-3"><!></div>'),_p=h('<span class="text-dl-text"> </span>'),wp=h('<div class="mt-3 space-y-3"><div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3"><div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div> <div class="text-[11px] text-dl-text-muted"> <!></div></div> <pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words"> </pre></div>'),yp=h('<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words"> </pre>'),kp=h('<div class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"><div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col"><div class="flex-shrink-0 border-b border-dl-border/50"><div class="flex items-center justify-between px-5 pt-4 pb-3"><div class="flex items-center gap-2 text-[14px] font-medium text-dl-text"><!> <span> </span> <!></div> <div class="flex items-center gap-2"><!> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <!> <!></div> <div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0"><!></div></div></div>'),Cp=h("<!> <!>",1);function Sp(e,t){rn(t,!0);let r=G(null),a=G("context"),s=G("raw"),o=B(()=>{var A,re,Y,X,ge,Z;if(!t.message.loading)return"";if(t.message.text)return"응답 작성 중";if(((A=t.message.toolEvents)==null?void 0:A.length)>0){const oe=[...t.message.toolEvents].reverse().find(Bt=>Bt.type==="call"),ct=((re=oe==null?void 0:oe.arguments)==null?void 0:re.module)||((Y=oe==null?void 0:oe.arguments)==null?void 0:Y.keyword)||"";return`도구 실행 중 — ${(oe==null?void 0:oe.name)||""}${ct?` (${ct})`:""}`}if(((X=t.message.contexts)==null?void 0:X.length)>0){const oe=t.message.contexts[t.message.contexts.length-1];return`데이터 분석 중 — ${(oe==null?void 0:oe.label)||(oe==null?void 0:oe.module)||""}`}return t.message.snapshot?"핵심 수치 확인 완료, 데이터 검색 중":(ge=t.message.meta)!=null&&ge.company?`${t.message.meta.company} 데이터 검색 중`:(Z=t.message.meta)!=null&&Z.includedModules?"분석 모듈 선택 완료":"생각 중"}),i=B(()=>{var A;return t.message.company||((A=t.message.meta)==null?void 0:A.company)||null});const l={capability:"기능 탐색",coding:"코딩 작업",company_explore:"회사 탐색",company_analysis:"회사 분석",follow_up:"후속 질문",general_chat:"일반 대화"};let c=B(()=>{var A;return(A=t.message.meta)!=null&&A.dialogueMode?l[t.message.meta.dialogueMode]||t.message.meta.dialogueMode:null}),f=B(()=>{var A,re,Y;return t.message.systemPrompt||t.message.userContent||((A=t.message.contexts)==null?void 0:A.length)>0||((re=t.message.meta)==null?void 0:re.includedModules)||((Y=t.message.toolEvents)==null?void 0:Y.length)>0}),p=B(()=>{var re;const A=(re=t.message.meta)==null?void 0:re.dataYearRange;return A?typeof A=="string"?A:A.min_year&&A.max_year?`${A.min_year}~${A.max_year}년`:null:null});function b(A){if(!A)return 0;const re=(A.match(/[\uac00-\ud7af]/g)||[]).length,Y=A.length-re;return Math.round(re*1.5+Y/3.5)}function _(A){return A>=1e3?(A/1e3).toFixed(1)+"k":String(A)}let z=B(()=>{var re;let A=0;if(t.message.systemPrompt&&(A+=b(t.message.systemPrompt)),t.message.userContent)A+=b(t.message.userContent);else if(((re=t.message.contexts)==null?void 0:re.length)>0)for(const Y of t.message.contexts)A+=b(Y.text);return A}),y=B(()=>b(t.message.text)),I=G(void 0);const k=/^\s*\|.+\|\s*$/;function C(A,re){if(!A)return{committed:"",draft:"",draftType:"none"};if(!re)return{committed:A,draft:"",draftType:"none"};const Y=A.split(`
`);let X=Y.length;A.endsWith(`
`)||(X=Math.min(X,Y.length-1));let ge=0,Z=-1;for(let wt=0;wt<Y.length;wt++)Y[wt].trim().startsWith("```")&&(ge+=1,Z=wt);ge%2===1&&Z>=0&&(X=Math.min(X,Z));let oe=-1;for(let wt=Y.length-1;wt>=0;wt--){const er=Y[wt];if(!er.trim())break;if(k.test(er))oe=wt;else{oe=-1;break}}if(oe>=0&&(X=Math.min(X,oe)),X<=0)return{committed:"",draft:A,draftType:oe===0?"table":ge%2===1?"code":"text"};const ct=Y.slice(0,X).join(`
`),Bt=Y.slice(X).join(`
`);let Rt="text";return Bt&&oe>=X?Rt="table":Bt&&ge%2===1&&(Rt="code"),{committed:ct,draft:Bt,draftType:Rt}}const L='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',U='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';function S(A){var ge;const re=A.target.closest(".code-copy-btn");if(!re)return;const Y=re.closest(".code-block-wrap"),X=((ge=Y==null?void 0:Y.querySelector("code"))==null?void 0:ge.textContent)||"";navigator.clipboard.writeText(X).then(()=>{re.innerHTML=U,setTimeout(()=>{re.innerHTML=L},2e3)})}function q(A){if(t.onOpenEvidence){t.onOpenEvidence("contexts",A);return}u(r,A,!0),u(a,"context"),u(s,"rendered")}function le(){if(t.onOpenEvidence){t.onOpenEvidence("system");return}u(r,0),u(a,"system"),u(s,"raw")}function $(){if(t.onOpenEvidence){t.onOpenEvidence("snapshot");return}u(r,0),u(a,"snapshot")}function x(A){var re;if(t.onOpenEvidence){const Y=(re=t.message.toolEvents)==null?void 0:re[A];t.onOpenEvidence((Y==null?void 0:Y.type)==="result"?"tool-results":"tool-calls",A);return}u(r,A,!0),u(a,"tool"),u(s,"raw")}function H(){if(t.onOpenEvidence){t.onOpenEvidence("input");return}u(r,0),u(a,"userContent"),u(s,"raw")}function te(){u(r,null)}function K(A){var re,Y,X,ge;return A?A.type==="call"?((re=A.arguments)==null?void 0:re.module)||((Y=A.arguments)==null?void 0:Y.keyword)||((X=A.arguments)==null?void 0:X.engine)||((ge=A.arguments)==null?void 0:ge.name)||"":typeof A.result=="string"?A.result.slice(0,120):A.result&&typeof A.result=="object"&&(A.result.module||A.result.status||A.result.name)||"":""}let T=B(()=>(t.message.toolEvents||[]).filter(A=>A.type==="call")),ie=B(()=>(t.message.toolEvents||[]).filter(A=>A.type==="result")),fe=B(()=>C(t.message.text||"",t.message.loading)),be=B(()=>{var re,Y,X;const A=[];return((Y=(re=t.message.meta)==null?void 0:re.includedModules)==null?void 0:Y.length)>0&&A.push({label:`모듈 ${t.message.meta.includedModules.length}개`,icon:ps}),((X=t.message.contexts)==null?void 0:X.length)>0&&A.push({label:`컨텍스트 ${t.message.contexts.length}건`,icon:ov}),n(T).length>0&&A.push({label:`툴 호출 ${n(T).length}건`,icon:Vi}),n(ie).length>0&&A.push({label:`툴 결과 ${n(ie).length}건`,icon:_s}),t.message.systemPrompt&&A.push({label:"시스템 프롬프트",icon:uo}),t.message.userContent&&A.push({label:"LLM 입력",icon:jn}),A}),ve=B(()=>{var re,Y,X;if(!t.message.loading)return[];const A=[];return(re=t.message.meta)!=null&&re.company&&A.push({label:`${t.message.meta.company} 인식`,done:!0}),t.message.snapshot&&A.push({label:"핵심 수치 확인",done:!0}),(Y=t.message.meta)!=null&&Y.includedModules&&A.push({label:`모듈 ${t.message.meta.includedModules.length}개 선택`,done:!0}),((X=t.message.contexts)==null?void 0:X.length)>0&&A.push({label:`데이터 ${t.message.contexts.length}건 로드`,done:!0}),t.message.systemPrompt&&A.push({label:"프롬프트 조립",done:!0}),t.message.text?A.push({label:"응답 작성 중",done:!1}):A.push({label:n(o)||"준비 중",done:!1}),A});var Ae=Cp(),me=ee(Ae);{var he=A=>{var re=Dv(),Y=m(d(re),2),X=d(Y),ge=d(X);N(()=>P(ge,t.message.text)),v(A,re)},W=A=>{var re=up(),Y=m(d(re),2),X=d(Y);{var ge=Ct=>{var Oe=Fv(),gt=d(Oe),fr=d(gt);Jf(fr,{size:11});var Dt=m(gt,4),vt=d(Dt);{var Tt=Ne=>{ms(Ne,{variant:"muted",children:(Ce,pt)=>{var Se=ta();N(()=>P(Se,n(i))),v(Ce,Se)},$$slots:{default:!0}})};E(vt,Ne=>{n(i)&&Ne(Tt)})}var w=m(vt,2);{var j=Ne=>{ms(Ne,{variant:"muted",children:(Ce,pt)=>{var Se=ta();N(We=>P(Se,We),[()=>t.message.meta.market.toUpperCase()]),v(Ce,Se)},$$slots:{default:!0}})};E(w,Ne=>{var Ce;(Ce=t.message.meta)!=null&&Ce.market&&Ne(j)})}var O=m(w,2);{var J=Ne=>{ms(Ne,{variant:"accent",children:(Ce,pt)=>{var Se=ta();N(()=>P(Se,n(c))),v(Ce,Se)},$$slots:{default:!0}})};E(O,Ne=>{n(c)&&Ne(J)})}var F=m(O,2);{var ze=Ne=>{ms(Ne,{variant:"muted",children:(Ce,pt)=>{var Se=ta();N(()=>P(Se,t.message.meta.topicLabel)),v(Ce,Se)},$$slots:{default:!0}})};E(F,Ne=>{var Ce;(Ce=t.message.meta)!=null&&Ce.topicLabel&&Ne(ze)})}var Re=m(F,2);{var wr=Ne=>{ms(Ne,{variant:"accent",children:(Ce,pt)=>{var Se=ta();N(()=>P(Se,n(p))),v(Ce,Se)},$$slots:{default:!0}})};E(Re,Ne=>{n(p)&&Ne(wr)})}var rt=m(Re,2);{var Yt=Ne=>{var Ce=ye(),pt=ee(Ce);Ie(pt,17,()=>t.message.contexts,Te,(Se,We,Ke)=>{var yt=jv(),Q=d(yt);ps(Q,{size:10,class:"flex-shrink-0"});var qe=m(Q);N(()=>P(qe,` ${(n(We).label||n(We).module)??""}`)),ae("click",yt,()=>q(Ke)),v(Se,yt)}),v(Ne,Ce)},tr=Ne=>{var Ce=Vv(),pt=d(Ce);ps(pt,{size:10,class:"flex-shrink-0"});var Se=m(pt);N(()=>P(Se,` 모듈 ${t.message.meta.includedModules.length??""}개`)),v(Ne,Ce)};E(rt,Ne=>{var Ce,pt,Se;((Ce=t.message.contexts)==null?void 0:Ce.length)>0?Ne(Yt):((Se=(pt=t.message.meta)==null?void 0:pt.includedModules)==null?void 0:Se.length)>0&&Ne(tr,1)})}var Ur=m(rt,2);Ie(Ur,17,()=>n(be),Te,(Ne,Ce)=>{var pt=qv(),Se=d(pt);wu(Se,()=>n(Ce).icon,(Ke,yt)=>{yt(Ke,{size:10,class:"flex-shrink-0"})});var We=m(Se);N(()=>P(We,` ${n(Ce).label??""}`)),ae("click",pt,()=>{n(Ce).label.startsWith("컨텍스트")?q(0):n(Ce).label.startsWith("툴 호출")?t.onOpenEvidence?t.onOpenEvidence("tool-calls",0):x(0):n(Ce).label.startsWith("툴 결과")?t.onOpenEvidence?t.onOpenEvidence("tool-results",0):x((t.message.toolEvents||[]).findIndex(Ke=>Ke.type==="result")):n(Ce).label==="시스템 프롬프트"?le():n(Ce).label==="LLM 입력"&&H()}),v(Ne,pt)}),v(Ct,Oe)};E(X,Ct=>{var Oe,gt;(n(i)||n(p)||((Oe=t.message.contexts)==null?void 0:Oe.length)>0||(gt=t.message.meta)!=null&&gt.includedModules||n(be).length>0)&&Ct(ge)})}var Z=m(X,2);{var oe=Ct=>{var Oe=Uv(),gt=d(Oe);Ie(gt,21,()=>t.message.snapshot.items,Te,(vt,Tt)=>{const w=B(()=>n(Tt).status==="good"?"text-dl-success":n(Tt).status==="danger"?"text-dl-primary-light":n(Tt).status==="caution"?"text-amber-400":"text-dl-text");var j=Bv(),O=d(j),J=d(O),F=m(O,2),ze=d(F);N(Re=>{P(J,n(Tt).label),Le(F,1,Re),P(ze,n(Tt).value)},[()=>Pt(Nt("text-[14px] font-semibold leading-snug mt-0.5",n(w)))]),v(vt,j)});var fr=m(gt,2);{var Dt=vt=>{var Tt=Hv();Ie(Tt,21,()=>t.message.snapshot.warnings,Te,(w,j)=>{var O=Gv(),J=d(O);hv(J,{size:10});var F=m(J);N(()=>P(F,` ${n(j)??""}`)),v(w,O)}),v(vt,Tt)};E(fr,vt=>{var Tt;((Tt=t.message.snapshot.warnings)==null?void 0:Tt.length)>0&&vt(Dt)})}ae("click",Oe,$),v(Ct,Oe)};E(Z,Ct=>{var Oe,gt;((gt=(Oe=t.message.snapshot)==null?void 0:Oe.items)==null?void 0:gt.length)>0&&Ct(oe)})}var ct=m(Z,2);{var Bt=Ct=>{var Oe=Kv(),gt=d(Oe),fr=m(d(gt),4);Ie(fr,21,()=>t.message.toolEvents,Te,(Dt,vt,Tt)=>{const w=B(()=>K(n(vt)));var j=Wv(),O=d(j);{var J=Re=>{Vi(Re,{size:11})},F=Re=>{_s(Re,{size:11})};E(O,Re=>{n(vt).type==="call"?Re(J):Re(F,-1)})}var ze=m(O);N(Re=>{Le(j,1,Re),P(ze,` ${(n(vt).type==="call"?n(vt).name:`${n(vt).name} 결과`)??""}${n(w)?`: ${n(w)}`:""}`)},[()=>Pt(Nt("flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all",n(vt).type==="call"?"border-dl-accent/30 bg-dl-accent/[0.06] text-dl-accent hover:border-dl-accent/50":"border-dl-success/30 bg-dl-success/[0.06] text-dl-success hover:border-dl-success/50"))]),ae("click",j,()=>x(Tt)),v(Dt,j)}),v(Ct,Oe)};E(ct,Ct=>{var Oe;((Oe=t.message.toolEvents)==null?void 0:Oe.length)>0&&Ct(Bt)})}var Rt=m(ct,2);{var wt=Ct=>{var Oe=Qv(),gt=d(Oe);Ie(gt,21,()=>n(ve),Te,(fr,Dt)=>{var vt=Jv(),Tt=d(vt);{var w=O=>{var J=Yv(),F=m(ee(J),2),ze=d(F);N(()=>P(ze,n(Dt).label)),v(O,J)},j=O=>{var J=Xv(),F=ee(J);vn(F,{size:14,class:"animate-spin flex-shrink-0 text-dl-text-dim"});var ze=m(F,2),Re=d(ze);N(()=>P(Re,n(Dt).label)),v(O,J)};E(Tt,O=>{n(Dt).done?O(w):O(j,-1)})}v(fr,vt)}),v(Ct,Oe)},er=Ct=>{var Oe=cp(),gt=ee(Oe);{var fr=F=>{var ze=Zv(),Re=d(ze);vn(Re,{size:12,class:"animate-spin flex-shrink-0"});var wr=m(Re,2),rt=d(wr);N(()=>P(rt,n(o))),v(F,ze)};E(gt,F=>{t.message.loading&&F(fr)})}var Dt=m(gt,2),vt=d(Dt);{var Tt=F=>{var ze=ep(),Re=d(ze);oa(Re,()=>es(n(fe).committed)),v(F,ze)};E(vt,F=>{n(fe).committed&&F(Tt)})}var w=m(vt,2);{var j=F=>{var ze=tp(),Re=d(ze),wr=d(Re),rt=m(Re,2),Yt=d(rt);N(tr=>{Le(ze,1,tr),P(wr,n(fe).draftType==="table"?"표 구성 중":n(fe).draftType==="code"?"코드 블록 생성 중":"응답 작성 중"),P(Yt,n(fe).draft)},[()=>Pt(Nt("message-live-tail",n(fe).draftType==="table"&&"message-draft-table",n(fe).draftType==="code"&&"message-draft-code"))]),v(F,ze)};E(w,F=>{n(fe).draft&&F(j)})}Aa(Dt,F=>u(I,F),()=>n(I));var O=m(Dt,2);{var J=F=>{var ze=dp(),Re=d(ze);{var wr=We=>{var Ke=rp(),yt=d(Ke);nv(yt,{size:10});var Q=m(yt);N(()=>P(Q,` ${t.message.duration??""}초`)),v(We,Ke)};E(Re,We=>{t.message.duration&&We(wr)})}var rt=m(Re,2);{var Yt=We=>{var Ke=sp(),yt=d(Ke);{var Q=nt=>{var xt=np(),De=d(xt);N(bt=>P(De,`↑${bt??""}`),[()=>_(n(z))]),v(nt,xt)};E(yt,nt=>{n(z)>0&&nt(Q)})}var qe=m(yt,2);{var ut=nt=>{var xt=ap(),De=d(xt);N(bt=>P(De,`↓${bt??""}`),[()=>_(n(y))]),v(nt,xt)};E(qe,nt=>{n(y)>0&&nt(ut)})}v(We,Ke)};E(rt,We=>{(n(z)>0||n(y)>0)&&We(Yt)})}var tr=m(rt,2);{var Ur=We=>{var Ke=op(),yt=d(Ke);uv(yt,{size:10}),ae("click",Ke,()=>{var Q;return(Q=t.onRegenerate)==null?void 0:Q.call(t)}),v(We,Ke)};E(tr,We=>{t.onRegenerate&&We(Ur)})}var Ne=m(tr,2);{var Ce=We=>{var Ke=ip(),yt=d(Ke);uo(yt,{size:10}),ae("click",Ke,le),v(We,Ke)};E(Ne,We=>{t.message.systemPrompt&&We(Ce)})}var pt=m(Ne,2);{var Se=We=>{var Ke=lp(),yt=d(Ke);jn(yt,{size:10});var Q=m(yt);N((qe,ut)=>P(Q,` LLM 입력 (${qe??""}자 · ~${ut??""}tok)`),[()=>t.message.userContent.length.toLocaleString(),()=>_(b(t.message.userContent))]),ae("click",Ke,H),v(We,Ke)};E(pt,We=>{t.message.userContent&&We(Se)})}v(F,ze)};E(O,F=>{!t.message.loading&&(t.message.duration||n(f)||t.onRegenerate)&&F(J)})}N(F=>Le(Dt,1,F),[()=>Pt(Nt("prose-dartlab message-body text-[15px] leading-[1.75]",t.message.error&&"text-dl-primary"))]),ae("click",Dt,S),v(Ct,Oe)};E(Rt,Ct=>{t.message.loading&&!t.message.text?Ct(wt):Ct(er,-1)})}v(A,re)};E(me,A=>{t.message.role==="user"?A(he):A(W,-1)})}var tt=m(me,2);{var ke=A=>{const re=B(()=>n(a)==="system"),Y=B(()=>n(a)==="userContent"),X=B(()=>n(a)==="context"),ge=B(()=>n(a)==="snapshot"),Z=B(()=>n(a)==="tool"),oe=B(()=>{var Q;return n(X)?(Q=t.message.contexts)==null?void 0:Q[n(r)]:null}),ct=B(()=>{var Q;return n(Z)?(Q=t.message.toolEvents)==null?void 0:Q[n(r)]:null}),Bt=B(()=>{var Q,qe,ut,nt,xt;return n(ge)?"핵심 수치 (원본 데이터)":n(re)?"시스템 프롬프트":n(Y)?"LLM에 전달된 입력":n(Z)?((Q=n(ct))==null?void 0:Q.type)==="call"?`${(qe=n(ct))==null?void 0:qe.name} 호출`:`${(ut=n(ct))==null?void 0:ut.name} 결과`:((nt=n(oe))==null?void 0:nt.label)||((xt=n(oe))==null?void 0:xt.module)||""}),Rt=B(()=>{var Q;return n(ge)?JSON.stringify(t.message.snapshot,null,2):n(re)?t.message.systemPrompt:n(Y)?t.message.userContent:n(Z)?JSON.stringify(n(ct),null,2):(Q=n(oe))==null?void 0:Q.text});var wt=kp(),er=d(wt),Ct=d(er),Oe=d(Ct),gt=d(Oe),fr=d(gt);{var Dt=Q=>{ps(Q,{size:15,class:"text-dl-success flex-shrink-0"})},vt=Q=>{uo(Q,{size:15,class:"text-dl-primary-light flex-shrink-0"})},Tt=Q=>{jn(Q,{size:15,class:"text-dl-accent flex-shrink-0"})},w=Q=>{ps(Q,{size:15,class:"flex-shrink-0"})};E(fr,Q=>{n(ge)?Q(Dt):n(re)?Q(vt,1):n(Y)?Q(Tt,2):Q(w,-1)})}var j=m(fr,2),O=d(j),J=m(j,2);{var F=Q=>{var qe=fp(),ut=d(qe);N(nt=>P(ut,`(${nt??""}자)`),[()=>{var nt,xt;return(xt=(nt=n(Rt))==null?void 0:nt.length)==null?void 0:xt.toLocaleString()}]),v(Q,qe)};E(J,Q=>{n(re)&&Q(F)})}var ze=m(gt,2),Re=d(ze);{var wr=Q=>{var qe=vp(),ut=d(qe),nt=d(ut);jn(nt,{size:11});var xt=m(ut,2),De=d(xt);av(De,{size:11}),N((bt,$t)=>{Le(ut,1,bt),Le(xt,1,$t)},[()=>Pt(Nt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="rendered"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted")),()=>Pt(Nt("flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",n(s)==="raw"?"bg-dl-bg-card text-dl-text shadow-sm":"text-dl-text-dim hover:text-dl-text-muted"))]),ae("click",ut,()=>u(s,"rendered")),ae("click",xt,()=>u(s,"raw")),v(Q,qe)};E(Re,Q=>{n(X)&&Q(wr)})}var rt=m(Re,2),Yt=d(rt);Bs(Yt,{size:18});var tr=m(Oe,2);{var Ur=Q=>{var qe=mp(),ut=d(qe);Ie(ut,21,()=>t.message.contexts,Te,(nt,xt,De)=>{var bt=pp(),$t=d(bt);N(Gt=>{Le(bt,1,Gt),P($t,t.message.contexts[De].label||t.message.contexts[De].module)},[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",De===n(r)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"))]),ae("click",bt,()=>{u(r,De,!0)}),v(nt,bt)}),v(Q,qe)};E(tr,Q=>{var qe;n(X)&&((qe=t.message.contexts)==null?void 0:qe.length)>1&&Q(Ur)})}var Ne=m(tr,2);{var Ce=Q=>{var qe=xp(),ut=d(qe),nt=d(ut);{var xt=$t=>{var Gt=hp();N(Wr=>Le(Gt,1,Wr),[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(re)?"bg-dl-primary/20 text-dl-primary-light font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ae("click",Gt,()=>{u(a,"system")}),v($t,Gt)};E(nt,$t=>{t.message.systemPrompt&&$t(xt)})}var De=m(nt,2);{var bt=$t=>{var Gt=gp();N(Wr=>Le(Gt,1,Wr),[()=>Pt(Nt("px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",n(Y)?"bg-dl-accent/20 text-dl-accent font-medium":"bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"))]),ae("click",Gt,()=>{u(a,"userContent")}),v($t,Gt)};E(De,$t=>{t.message.userContent&&$t(bt)})}v(Q,qe)};E(Ne,Q=>{!n(X)&&!n(ge)&&!n(Z)&&Q(Ce)})}var pt=m(Ct,2),Se=d(pt);{var We=Q=>{var qe=bp(),ut=d(qe);oa(ut,()=>{var nt;return es((nt=n(oe))==null?void 0:nt.text)}),v(Q,qe)},Ke=Q=>{var qe=wp(),ut=d(qe),nt=m(d(ut),2),xt=d(nt),De=m(xt);{var bt=jt=>{var an=_p(),Gn=d(an);N(sn=>P(Gn,sn),[()=>K(n(ct))]),v(jt,an)},$t=B(()=>K(n(ct)));E(De,jt=>{n($t)&&jt(bt)})}var Gt=m(ut,2),Wr=d(Gt);N(()=>{var jt;P(xt,`${((jt=n(ct))==null?void 0:jt.type)==="call"?"LLM이 도구를 호출한 이벤트입니다.":"도구 실행 결과가 반환된 이벤트입니다."} `),P(Wr,n(Rt))}),v(Q,qe)},yt=Q=>{var qe=yp(),ut=d(qe);N(()=>P(ut,n(Rt))),v(Q,qe)};E(Se,Q=>{n(X)&&n(s)==="rendered"?Q(We):n(Z)?Q(Ke,1):Q(yt,-1)})}N(()=>P(O,n(Bt))),ae("click",wt,Q=>{Q.target===Q.currentTarget&&te()}),ae("keydown",wt,Q=>{Q.key==="Escape"&&te()}),ae("click",rt,te),v(A,wt)};E(tt,A=>{n(r)!==null&&A(ke)})}v(e,Ae),nn()}Bn(["click","keydown"]);var Mp=h('<div class="pointer-events-none absolute bottom-28 right-6 z-20"><button class="pointer-events-auto surface-overlay rounded-full border border-dl-primary/20 bg-dl-bg-card/92 px-3 py-2 text-[11px] font-medium text-dl-text shadow-lg shadow-black/30 transition-all hover:-translate-y-0.5 hover:border-dl-primary/40 hover:text-dl-primary-light">최신 응답으로 이동</button></div>'),Ep=h('<button class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"><!> 마크다운</button>'),Ap=h('<div class="flex justify-end gap-2 mb-1.5"><!></div>'),zp=h('<div class="relative flex flex-col h-full min-h-0"><div class="flex-1 overflow-y-auto min-h-0"><div class="chat-stream-shell max-w-[760px] mx-auto px-5 pt-5 pb-10 space-y-8"><!> <div class="h-px w-full"></div></div></div> <!> <div class="flex-shrink-0 px-5 pb-4 pt-2"><div class="max-w-[720px] mx-auto"><!> <!></div></div></div>');function Tp(e,t){rn(t,!0);function r(K){if(s())return!1;for(let T=a().length-1;T>=0;T--)if(a()[T].role==="assistant"&&!a()[T].error&&a()[T].text)return T===K;return!1}let a=dt(t,"messages",19,()=>[]),s=dt(t,"isLoading",3,!1),o=dt(t,"inputText",15,""),i=dt(t,"scrollTrigger",3,0);dt(t,"selectedCompany",3,null);function l(K){return(T,ie)=>{var be,ve,Ae,me;(be=t.onOpenEvidence)==null||be.call(t,T,ie);let fe;if(T==="contexts")fe=(ve=K.contexts)==null?void 0:ve[ie];else if(T==="snapshot")fe={label:"핵심 수치",module:"snapshot",text:JSON.stringify(K.snapshot,null,2)};else if(T==="system")fe={label:"시스템 프롬프트",module:"system",text:K.systemPrompt};else if(T==="input")fe={label:"LLM 입력",module:"input",text:K.userContent};else if(T==="tool-calls"||T==="tool-results"){const he=(Ae=K.toolEvents)==null?void 0:Ae[ie];fe={label:`${(he==null?void 0:he.name)||"도구"} ${(he==null?void 0:he.type)==="call"?"호출":"결과"}`,module:"tool",text:JSON.stringify(he,null,2)}}fe&&((me=t.onOpenData)==null||me.call(t,fe))}}let c,f,p=G(!0),b=G(!1),_=G(!0);function z(){if(!c)return;const{scrollTop:K,scrollHeight:T,clientHeight:ie}=c;u(_,T-K-ie<96),n(_)?(u(p,!0),u(b,!1)):(u(p,!1),u(b,!0))}function y(K="smooth"){f&&(f.scrollIntoView({block:"end",behavior:K}),u(p,!0),u(b,!1))}Dn(()=>{i(),!(!c||!f)&&requestAnimationFrame(()=>{!c||!f||(n(p)||n(_)?(f.scrollIntoView({block:"end",behavior:s()?"auto":"smooth"}),u(b,!1)):u(b,!0))})});var I=zp(),k=d(I),C=d(k),L=d(C);Ie(L,17,a,Te,(K,T,ie)=>{{let fe=B(()=>r(ie)?t.onRegenerate:void 0),be=B(()=>t.onOpenData?l(n(T)):void 0);Sp(K,{get message(){return n(T)},get onRegenerate(){return n(fe)},get onOpenEvidence(){return n(be)}})}});var U=m(L,2);Aa(U,K=>f=K,()=>f),Aa(k,K=>c=K,()=>c);var S=m(k,2);{var q=K=>{var T=Mp(),ie=d(T);ae("click",ie,()=>y("smooth")),v(K,T)};E(S,K=>{n(b)&&K(q)})}var le=m(S,2),$=d(le),x=d($);{var H=K=>{var T=Ap(),ie=d(T);{var fe=be=>{var ve=Ep(),Ae=d(ve);ws(Ae,{size:10}),ae("click",ve,function(...me){var he;(he=t.onExport)==null||he.apply(this,me)}),v(be,ve)};E(ie,be=>{a().length>1&&t.onExport&&be(fe)})}v(K,T)};E(x,K=>{s()||K(H)})}var te=m(x,2);ld(te,{get isLoading(){return s()},placeholder:"메시지를 입력하세요...",get onSend(){return t.onSend},get onStop(){return t.onStop},get onCompanySelect(){return t.onCompanySelect},get inputText(){return o()},set inputText(K){o(K)}}),Va("scroll",k,z),v(e,I),nn()}Bn(["click"]);var Ip=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!> <span class="text-[13px]">공시 데이터 로딩 중...</span></div>'),Pp=h('<div class="text-[11px] text-dl-text-dim"> </div>'),Np=h('<button><!> <span class="truncate flex-1"> </span></button>'),$p=h('<div class="py-0.5"></div>'),Lp=h('<div><button class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"><!> <span class="truncate"> </span> <span class="ml-auto text-[9px] opacity-30 font-normal"> </span></button> <!></div>'),Op=h('<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50"><div class="px-3 py-2.5 border-b border-dl-border/20"><!></div> <!></nav>'),Rp=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim"><!> <p class="text-[13px]">좌측에서 섹션을 선택하세요</p></div>'),Dp=h('<div class="text-[10px] text-dl-text-dim/50 mb-0.5"> </div>'),jp=h('<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim"><!></div>'),Vp=h('<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>'),qp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Fp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Bp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Gp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Hp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Up=h('<div class="vw-heading-node svelte-1l2nqwu"><!></div>'),Wp=h('<div class="vw-heading-block svelte-1l2nqwu"></div>'),Kp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Yp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Xp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Jp=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),Qp=h('<button><span class="vw-timeline-label svelte-1l2nqwu"> </span></button>'),Zp=h('<div class="vw-section-timeline svelte-1l2nqwu"></div>'),em=h('<span class="vw-meta-pill svelte-1l2nqwu"> </span>'),tm=h('<span class="vw-meta-pill svelte-1l2nqwu">비교 없음</span>'),rm=h('<div class="vw-section-actions svelte-1l2nqwu"><span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span></div>'),nm=h('<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span> </div>'),am=h('<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),sm=h('<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5"><span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span> <span class="flex-1"> </span></div>'),om=h('<div class="text-[10px] text-dl-text-dim/35 mt-1"> </div>'),im=h('<div class="vw-digest svelte-1l2nqwu"><div class="flex items-center gap-2 mb-2"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span></div> <div class="space-y-1"><!> <!> <!> <!></div></div>'),lm=h('<p class="vw-para"> </p>'),dm=h('<div class="vw-diff-added svelte-1l2nqwu"> </div>'),cm=h('<div class="vw-diff-deleted svelte-1l2nqwu"> </div>'),um=h('<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow svelte-1l2nqwu"></div>'),fm=h('<div class="disclosure-text vw-section-body vw-body-frame svelte-1l2nqwu"><!></div>'),vm=h('<div><!> <div class="vw-section-meta svelte-1l2nqwu"><span> </span> <!> <!> <!> <!></div> <!> <!> <!> <!></div>'),pm=h('<section class="vw-report-shell svelte-1l2nqwu"><div class="vw-report-header svelte-1l2nqwu"><div class="vw-report-badges svelte-1l2nqwu"><!> <!> <span class="vw-meta-pill svelte-1l2nqwu"> </span> <!> <!> <!></div></div> <!></section>'),mm=h('<div class="vw-data-divider svelte-1l2nqwu"><div class="vw-data-kicker svelte-1l2nqwu">Structured Data</div> <div class="vw-data-title svelte-1l2nqwu">표 / 정형 데이터</div></div>'),hm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),gm=h("<th> </th>"),xm=h("<td> </td>"),bm=h("<tr></tr>"),_m=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),wm=h('<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1"> </div>'),ym=h("<th> </th>"),km=h("<td> </td>"),Cm=h("<tr></tr>"),Sm=h('<!> <div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>',1),Mm=h("<button> </button>"),Em=h('<span class="text-[9px] text-dl-text-dim/30"> </span>'),Am=h('<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto"><!> <!></div>'),zm=h('<div class="vw-table-wrap bg-dl-bg-card/10 svelte-1l2nqwu"><!> <div class="px-4 py-3"><div class="markdown-table overflow-x-auto svelte-1l2nqwu"><!></div></div></div>'),Tm=h("<th> </th>"),Im=h("<td> </td>"),Pm=h("<tr></tr>"),Nm=h('<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02] svelte-1l2nqwu"><div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10"><!> <span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span></div> <div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),$m=h('<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card"> </th>'),Lm=h('<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted"> </td>'),Om=h("<tr></tr>"),Rm=h('<div class="vw-table-wrap svelte-1l2nqwu"><div class="overflow-x-auto"><table class="w-full border-collapse text-[12px]"><thead><tr></tr></thead><tbody></tbody></table></div></div>'),Dm=h('<article class="py-6 px-8"><!> <!> <!> <!></article>'),jm=h('<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center"><div class="flex-1 min-w-0"><!> <h3 class="text-[16px] font-semibold text-dl-text"> </h3></div> <button class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"><!></button></div> <!>',1),Vm=h('<div class="flex flex-1 overflow-hidden min-h-0"><!> <main class="flex-1 overflow-y-auto min-w-0"><!></main></div>'),qm=h('<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8"><!> <p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p></div>'),Fm=h('<div class="flex flex-col h-full font-sans bg-dl-bg-dark"><!></div>');function Bm(e,t){rn(t,!0);let r=dt(t,"stockCode",3,null),a=dt(t,"onTopicChange",3,null),s=G(null),o=G(!1),i=G(qt(new Set)),l=G(null),c=G(null),f=G(qt([])),p=G(null),b=G(!1),_=G(qt([])),z=G(qt(new Map)),y=new Map,I=G(!1),k=G(qt(new Map));const C={companyOverview:"회사 개요",companyHistory:"회사 연혁",articlesOfIncorporation:"정관 사항",capitalChange:"자본금 변동",shareCapital:"주식 현황",dividend:"배당",productService:"사업 내용",rawMaterial:"원재료",businessOverview:"사업 개요",salesOrder:"매출/수주",riskDerivative:"위험관리/파생",majorContractsAndRnd:"주요 계약/R&D",otherReferences:"기타 참고사항",consolidatedStatements:"연결 재무제표",fsSummary:"재무제표 요약",consolidatedNotes:"연결 주석",financialStatements:"개별 재무제표",financialNotes:"개별 주석",fundraising:"자금조달",BS:"재무상태표",IS:"손익계산서",CIS:"포괄손익계산서",CF:"현금흐름표",SCE:"자본변동표",ratios:"재무비율",audit:"감사 의견",mdna:"경영진 분석(MD&A)",internalControl:"내부통제",auditContract:"감사 계약",nonAuditContract:"비감사 계약",boardOfDirectors:"이사회",shareholderMeeting:"주주총회",auditSystem:"감사 체계",outsideDirector:"사외이사",majorHolder:"주요 주주",majorHolderChange:"주주 변동",minorityHolder:"소수주주",stockTotal:"주식 총수",treasuryStock:"자기주식",employee:"직원 현황",executivePay:"임원 보수",executive:"임원 현황",executivePayAllTotal:"전체 보수 총액",executivePayIndividual:"개인별 보수",topPay:"5억이상 상위 보수",unregisteredExecutivePay:"미등기임원 보수",affiliateGroup:"계열회사",investedCompany:"투자회사",relatedPartyTx:"특수관계 거래",corporateBond:"사채 관리",privateOfferingUsage:"사모자금 사용",publicOfferingUsage:"공모자금 사용",shortTermBond:"단기사채",investorProtection:"투자자 보호",disclosureChanges:"공시변경 사항",contingentLiability:"우발채무",sanction:"제재/조치",subsequentEvents:"후발사건",expertConfirmation:"전문가 확인",subsidiaryDetail:"종속회사 상세",affiliateGroupDetail:"계열회사 상세",investmentInOtherDetail:"타법인 출자 상세",rndDetail:"R&D 상세"},L={I:"I. 회사의 개요",II:"II. 사업의 내용",III:"III. 재무에 관한 사항",IV:"IV. 감사인의 감사의견 등",V:"V. 이사의 경영진단 및 분석의견",VI:"VI. 이사회 등 회사의 기관에 관한 사항",VII:"VII. 주주에 관한 사항",VIII:"VIII. 임원 및 직원 등에 관한 사항",IX:"IX. 계열회사 등에 관한 사항",X:"X. 대주주 등과의 거래내용",XI:"XI. 그 밖에 투자자 보호를 위하여 필요한 사항",XII:"XII. 상세표"},U={I:1,II:2,III:3,IV:4,V:5,VI:6,VII:7,VIII:8,IX:9,X:10,XI:11,XII:12};function S(w){return U[w]??99}function q(w){return C[w]||w}function le(w){return L[w]||w||"기타"}Dn(()=>{r()&&$()});async function $(){var w,j;u(o,!0),u(s,null),u(l,null),u(c,null),u(f,[],!0),u(p,null),y=new Map;try{const O=await Hu(r());u(s,O.payload,!0),(w=n(s))!=null&&w.columns&&u(_,n(s).columns.filter(F=>/^\d{4}(Q[1-4])?$/.test(F)),!0);const J=fe((j=n(s))==null?void 0:j.rows);J.length>0&&(u(i,new Set([J[0].chapter]),!0),J[0].topics.length>0&&x(J[0].topics[0].topic,J[0].chapter))}catch(O){console.error("viewer load error:",O)}u(o,!1)}async function x(w,j){var O;if(n(l)!==w){if(u(l,w,!0),u(c,j||null,!0),u(z,new Map,!0),u(k,new Map,!0),(O=a())==null||O(w,q(w)),y.has(w)){const J=y.get(w);u(f,J.blocks||[],!0),u(p,J.textDocument||null,!0);return}u(f,[],!0),u(p,null),u(b,!0);try{const J=await Gu(r(),w);u(f,J.blocks||[],!0),u(p,J.textDocument||null,!0),y.set(w,{blocks:n(f),textDocument:n(p)})}catch(J){console.error("topic load error:",J),u(f,[],!0),u(p,null)}u(b,!1)}}function H(w){const j=new Set(n(i));j.has(w)?j.delete(w):j.add(w),u(i,j,!0)}function te(w,j){const O=new Map(n(z));O.get(w)===j?O.delete(w):O.set(w,j),u(z,O,!0)}function K(w,j){const O=new Map(n(k));O.set(w,j),u(k,O,!0)}function T(w){return w==="updated"?"최근 수정":w==="new"?"신규":w==="stale"?"과거 유지":"유지"}function ie(w){return w==="updated"?"updated":w==="new"?"new":w==="stale"?"stale":"stable"}function fe(w){if(!w)return[];const j=new Map,O=new Set;for(const J of w){const F=J.chapter||"";j.has(F)||j.set(F,{chapter:F,topics:[]}),O.has(J.topic)||(O.add(J.topic),j.get(F).topics.push({topic:J.topic,source:J.source||"docs"}))}return[...j.values()].sort((J,F)=>S(J.chapter)-S(F.chapter))}function be(w){return String(w).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function ve(w){return String(w||"").replaceAll(" "," ").replace(/\s+/g," ").trim()}function Ae(w){return!w||w.length>88?!1:/^\[.+\]$/.test(w)||/^【.+】$/.test(w)||/^[IVX]+\.\s/.test(w)||/^\d+\.\s/.test(w)||/^[가-힣]\.\s/.test(w)||/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)}function me(w){return/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)?"h5":"h4"}function he(w){return/^\[.+\]$/.test(w)||/^【.+】$/.test(w)?"vw-h-bracket":/^\(\d+\)\s/.test(w)||/^\([가-힣]\)\s/.test(w)?"vw-h-sub":"vw-h-section"}function W(w){if(!w)return[];if(/^\|.+\|$/m.test(w)||/^#{1,3} /m.test(w)||/```/.test(w))return[{kind:"markdown",text:w}];const j=[];let O=[];const J=()=>{O.length!==0&&(j.push({kind:"paragraph",text:O.join(" ")}),O=[])};for(const F of String(w).split(`
`)){const ze=ve(F);if(!ze){J();continue}if(Ae(ze)){J(),j.push({kind:"heading",text:ze,tag:me(ze),className:he(ze)});continue}O.push(ze)}return J(),j}function tt(w){return w?w.kind==="annual"?`${w.year}Q4`:w.year&&w.quarter?`${w.year}Q${w.quarter}`:w.label||"":""}function ke(w){var J;const j=W(w);if(j.length===0)return"";if(((J=j[0])==null?void 0:J.kind)==="markdown")return es(w);let O="";for(const F of j){if(F.kind==="heading"){O+=`<${F.tag} class="${F.className}">${be(F.text)}</${F.tag}>`;continue}O+=`<p class="vw-para">${be(F.text)}</p>`}return O}function A(w){if(!w)return"";const j=w.trim().split(`
`).filter(J=>J.trim());let O="";for(const J of j){const F=J.trim();/^[가-힣]\.\s/.test(F)||/^\d+[-.]/.test(F)?O+=`<h4 class="vw-h-section">${F}</h4>`:/^\(\d+\)\s/.test(F)||/^\([가-힣]\)\s/.test(F)?O+=`<h5 class="vw-h-sub">${F}</h5>`:/^\[.+\]$/.test(F)||/^【.+】$/.test(F)?O+=`<h4 class="vw-h-bracket">${F}</h4>`:O+=`<h5 class="vw-h-sub">${F}</h5>`}return O}function re(w){var O;const j=n(z).get(w.id);return j&&((O=w==null?void 0:w.views)!=null&&O[j])?w.views[j]:(w==null?void 0:w.latest)||null}function Y(w,j){var J,F;const O=n(z).get(w.id);return O?O===j:((F=(J=w==null?void 0:w.latest)==null?void 0:J.period)==null?void 0:F.label)===j}function X(w){return n(z).has(w.id)}function ge(w){return w==="updated"?"변경 있음":w==="new"?"직전 없음":"직전과 동일"}function Z(w){var ze,Re,wr;if(!w)return[];const j=W(w.body);if(j.length===0||((ze=j[0])==null?void 0:ze.kind)==="markdown"||!((Re=w.prevPeriod)!=null&&Re.label)||!((wr=w.diff)!=null&&wr.length))return j;const O=[];for(const rt of w.diff)for(const Yt of rt.paragraphs||[])O.push({kind:rt.kind,text:ve(Yt)});const J=[];let F=0;for(const rt of j){if(rt.kind!=="paragraph"){J.push(rt);continue}for(;F<O.length&&O[F].kind==="removed";)J.push({kind:"removed",text:O[F].text}),F+=1;F<O.length&&["same","added"].includes(O[F].kind)?(J.push({kind:O[F].kind,text:O[F].text||rt.text}),F+=1):J.push({kind:"same",text:rt.text})}for(;F<O.length;)J.push({kind:O[F].kind,text:O[F].text}),F+=1;return J}function oe(w){return w==null?!1:/^-?[\d,.]+%?$/.test(String(w).trim().replace(/,/g,""))}function ct(w){return w==null?!1:/^-[\d.]+/.test(String(w).trim().replace(/,/g,""))}function Bt(w,j){if(w==null||w==="")return"";const O=typeof w=="number"?w:Number(String(w).replace(/,/g,""));if(isNaN(O))return String(w);if(j<=1)return O.toLocaleString("ko-KR");const J=O/j;return Number.isInteger(J)?J.toLocaleString("ko-KR"):J.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g,",")}function Rt(w){if(w==null||w==="")return"";const j=String(w).trim();if(j.includes(","))return j;const O=j.match(/^(-?\d+)(\.\d+)?(%?)$/);return O?O[1].replace(/\B(?=(\d{3})+(?!\d))/g,",")+(O[2]||"")+(O[3]||""):j}function wt(w){var j,O;return(j=n(s))!=null&&j.rows&&((O=n(s).rows.find(J=>J.topic===w))==null?void 0:O.chapter)||null}function er(w){const j=w.match(/^(\d{4})(Q([1-4]))?$/);if(!j)return"0000_0";const O=j[1],J=j[3]||"5";return`${O}_${J}`}function Ct(w){return[...w].sort((j,O)=>er(O).localeCompare(er(j)))}let Oe=B(()=>n(f).filter(w=>w.kind!=="text"));var gt=Fm(),fr=d(gt);{var Dt=w=>{var j=Ip(),O=d(j);vn(O,{size:18,class:"animate-spin"}),v(w,j)},vt=w=>{var j=Vm(),O=d(j);{var J=rt=>{var Yt=Op(),tr=d(Yt),Ur=d(tr);{var Ne=pt=>{var Se=Pp(),We=d(Se);N(()=>P(We,`${n(_).length??""}개 기간 · ${n(_)[0]??""} ~ ${n(_)[n(_).length-1]??""}`)),v(pt,Se)};E(Ur,pt=>{n(_).length>0&&pt(Ne)})}var Ce=m(tr,2);Ie(Ce,17,()=>fe(n(s).rows),Te,(pt,Se)=>{var We=Lp(),Ke=d(We),yt=d(Ke);{var Q=jt=>{tv(jt,{size:11,class:"flex-shrink-0 opacity-40"})},qe=B(()=>n(i).has(n(Se).chapter)),ut=jt=>{rv(jt,{size:11,class:"flex-shrink-0 opacity-40"})};E(yt,jt=>{n(qe)?jt(Q):jt(ut,-1)})}var nt=m(yt,2),xt=d(nt),De=m(nt,2),bt=d(De),$t=m(Ke,2);{var Gt=jt=>{var an=$p();Ie(an,21,()=>n(Se).topics,Te,(Gn,sn)=>{var Xt=Np(),Fe=d(Xt);{var yr=or=>{Zf(or,{size:11,class:"flex-shrink-0 text-blue-400/40"})},Pn=or=>{Li(or,{size:11,class:"flex-shrink-0 text-emerald-400/40"})},Hn=or=>{jn(or,{size:11,class:"flex-shrink-0 opacity-30"})};E(Fe,or=>{n(sn).source==="finance"?or(yr):n(sn).source==="report"?or(Pn,1):or(Hn,-1)})}var Un=m(Fe,2),Wn=d(Un);N(or=>{Le(Xt,1,`group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											${n(l)===n(sn).topic?"bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]":"text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent"}`),P(Wn,or)},[()=>q(n(sn).topic)]),ae("click",Xt,()=>x(n(sn).topic,n(Se).chapter)),v(Gn,Xt)}),v(jt,an)},Wr=B(()=>n(i).has(n(Se).chapter));E($t,jt=>{n(Wr)&&jt(Gt)})}N(jt=>{P(xt,jt),P(bt,n(Se).topics.length)},[()=>le(n(Se).chapter)]),ae("click",Ke,()=>H(n(Se).chapter)),v(pt,We)}),v(rt,Yt)};E(O,rt=>{n(I)||rt(J)})}var F=m(O,2),ze=d(F);{var Re=rt=>{var Yt=Rp(),tr=d(Yt);jn(tr,{size:32,strokeWidth:1,class:"opacity-20"}),v(rt,Yt)},wr=rt=>{var Yt=jm(),tr=ee(Yt),Ur=d(tr),Ne=d(Ur);{var Ce=De=>{var bt=Dp(),$t=d(bt);N(Gt=>P($t,Gt),[()=>le(n(c)||wt(n(l)))]),v(De,bt)},pt=B(()=>n(c)||wt(n(l)));E(Ne,De=>{n(pt)&&De(Ce)})}var Se=m(Ne,2),We=d(Se),Ke=m(Ur,2),yt=d(Ke);{var Q=De=>{id(De,{size:15})},qe=De=>{od(De,{size:15})};E(yt,De=>{n(I)?De(Q):De(qe,-1)})}var ut=m(tr,2);{var nt=De=>{var bt=jp(),$t=d(bt);vn($t,{size:16,class:"animate-spin"}),v(De,bt)},xt=De=>{var bt=Dm(),$t=d(bt);{var Gt=Xt=>{var Fe=Vp();v(Xt,Fe)};E($t,Xt=>{var Fe,yr;n(f).length===0&&!(((yr=(Fe=n(p))==null?void 0:Fe.sections)==null?void 0:yr.length)>0)&&Xt(Gt)})}var Wr=m($t,2);{var jt=Xt=>{var Fe=pm(),yr=d(Fe),Pn=d(yr),Hn=d(Pn);{var Un=at=>{var pe=qp(),Be=d(pe);N(ot=>P(Be,`최신 기준 ${ot??""}`),[()=>tt(n(p).latestPeriod)]),v(at,pe)};E(Hn,at=>{n(p).latestPeriod&&at(Un)})}var Wn=m(Hn,2);{var or=at=>{var pe=Fp(),Be=d(pe);N((ot,It)=>P(Be,`커버리지 ${ot??""}~${It??""}`),[()=>tt(n(p).firstPeriod),()=>tt(n(p).latestPeriod)]),v(at,pe)};E(Wn,at=>{n(p).firstPeriod&&at(or)})}var La=m(Wn,2),Jt=d(La),St=m(La,2);{var rr=at=>{var pe=Bp(),Be=d(pe);N(()=>P(Be,`최근 수정 ${n(p).updatedCount??""}개`)),v(at,pe)};E(St,at=>{n(p).updatedCount>0&&at(rr)})}var Ht=m(St,2);{var kr=at=>{var pe=Gp(),Be=d(pe);N(()=>P(Be,`신규 ${n(p).newCount??""}개`)),v(at,pe)};E(Ht,at=>{n(p).newCount>0&&at(kr)})}var Cr=m(Ht,2);{var Sr=at=>{var pe=Hp(),Be=d(pe);N(()=>P(Be,`과거 유지 ${n(p).staleCount??""}개`)),v(at,pe)};E(Cr,at=>{n(p).staleCount>0&&at(Sr)})}var Dr=m(yr,2);Ie(Dr,17,()=>n(p).sections,Te,(at,pe)=>{const Be=B(()=>re(n(pe))),ot=B(()=>X(n(pe)));var It=vm(),vr=d(It);{var Pe=Ee=>{var ue=Wp();Ie(ue,21,()=>n(pe).headingPath,Te,(lt,Et)=>{var R=Up(),V=d(R);oa(V,()=>A(n(Et).text)),v(lt,R)}),v(Ee,ue)};E(vr,Ee=>{var ue;((ue=n(pe).headingPath)==null?void 0:ue.length)>0&&Ee(Pe)})}var Je=m(vr,2),mt=d(Je),Lt=d(mt),Mt=m(mt,2);{var ir=Ee=>{var ue=Kp(),lt=d(ue);N(Et=>P(lt,`최신 ${Et??""}`),[()=>tt(n(pe).latestPeriod)]),v(Ee,ue)};E(Mt,Ee=>{var ue;(ue=n(pe).latestPeriod)!=null&&ue.label&&Ee(ir)})}var Kr=m(Mt,2);{var lr=Ee=>{var ue=Yp(),lt=d(ue);N(Et=>P(lt,`최초 ${Et??""}`),[()=>tt(n(pe).firstPeriod)]),v(Ee,ue)};E(Kr,Ee=>{var ue,lt;(ue=n(pe).firstPeriod)!=null&&ue.label&&n(pe).firstPeriod.label!==((lt=n(pe).latestPeriod)==null?void 0:lt.label)&&Ee(lr)})}var Tr=m(Kr,2);{var g=Ee=>{var ue=Xp(),lt=d(ue);N(()=>P(lt,`${n(pe).periodCount??""}기간`)),v(Ee,ue)};E(Tr,Ee=>{n(pe).periodCount>0&&Ee(g)})}var D=m(Tr,2);{var de=Ee=>{var ue=Jp(),lt=d(ue);N(()=>P(lt,`최근 변경 ${n(pe).latestChange??""}`)),v(Ee,ue)};E(D,Ee=>{n(pe).latestChange&&Ee(de)})}var _e=m(Je,2);{var Me=Ee=>{var ue=Zp();Ie(ue,21,()=>n(pe).timeline,Te,(lt,Et)=>{var R=Qp(),V=d(R),ce=d(V);N((we,xe)=>{Le(R,1,`vw-timeline-chip ${we??""}`,"svelte-1l2nqwu"),P(ce,xe)},[()=>Y(n(pe),n(Et).period.label)?"is-active":"",()=>tt(n(Et).period)]),ae("click",R,()=>te(n(pe).id,n(Et).period.label)),v(lt,R)}),v(Ee,ue)};E(_e,Ee=>{var ue;((ue=n(pe).timeline)==null?void 0:ue.length)>0&&Ee(Me)})}var $e=m(_e,2);{var st=Ee=>{var ue=rm(),lt=d(ue),Et=d(lt),R=m(lt,2);{var V=ht=>{var kt=em(),dr=d(kt);N(_t=>P(dr,`비교 ${_t??""}`),[()=>tt(n(Be).prevPeriod)]),v(ht,kt)},ce=ht=>{var kt=tm();v(ht,kt)};E(R,ht=>{var kt;(kt=n(Be).prevPeriod)!=null&&kt.label?ht(V):ht(ce,-1)})}var we=m(R,2),xe=d(we);N((ht,kt)=>{P(Et,`선택 ${ht??""}`),P(xe,kt)},[()=>tt(n(Be).period),()=>ge(n(Be).status)]),v(Ee,ue)};E($e,Ee=>{n(ot)&&n(Be)&&Ee(st)})}var it=m($e,2);{var Ut=Ee=>{const ue=B(()=>n(Be).digest);var lt=im(),Et=d(lt),R=d(Et),V=d(R),ce=m(Et,2),we=d(ce);Ie(we,17,()=>n(ue).items.filter(_t=>_t.kind==="numeric"),Te,(_t,Qt)=>{var Wt=nm(),At=m(d(Wt));N(()=>P(At,` ${n(Qt).text??""}`)),v(_t,Wt)});var xe=m(we,2);Ie(xe,17,()=>n(ue).items.filter(_t=>_t.kind==="added"),Te,(_t,Qt)=>{var Wt=am(),At=m(d(Wt),2),Vt=d(At);N(()=>P(Vt,n(Qt).text)),v(_t,Wt)});var ht=m(xe,2);Ie(ht,17,()=>n(ue).items.filter(_t=>_t.kind==="removed"),Te,(_t,Qt)=>{var Wt=sm(),At=m(d(Wt),2),Vt=d(At);N(()=>P(Vt,n(Qt).text)),v(_t,Wt)});var kt=m(ht,2);{var dr=_t=>{var Qt=om(),Wt=d(Qt);N(()=>P(Wt,`외 ${n(ue).wordingCount??""}건 문구 수정`)),v(_t,Qt)};E(kt,_t=>{n(ue).wordingCount>0&&_t(dr)})}N(()=>P(V,`${n(ue).to??""} vs ${n(ue).from??""}`)),v(Ee,lt)};E(it,Ee=>{var ue,lt,Et;n(ot)&&((Et=(lt=(ue=n(Be))==null?void 0:ue.digest)==null?void 0:lt.items)==null?void 0:Et.length)>0&&Ee(Ut)})}var xn=m(it,2);{var Nn=Ee=>{var ue=ye(),lt=ee(ue);{var Et=V=>{var ce=um();Ie(ce,21,()=>Z(n(Be)),Te,(we,xe)=>{var ht=ye(),kt=ee(ht);{var dr=At=>{var Vt=ye(),Ir=ee(Vt);oa(Ir,()=>A(n(xe).text)),v(At,Vt)},_t=At=>{var Vt=lm(),Ir=d(Vt);N(()=>P(Ir,n(xe).text)),v(At,Vt)},Qt=At=>{var Vt=dm(),Ir=d(Vt);N(()=>P(Ir,n(xe).text)),v(At,Vt)},Wt=At=>{var Vt=cm(),Ir=d(Vt);N(()=>P(Ir,n(xe).text)),v(At,Vt)};E(kt,At=>{n(xe).kind==="heading"?At(dr):n(xe).kind==="same"?At(_t,1):n(xe).kind==="added"?At(Qt,2):n(xe).kind==="removed"&&At(Wt,3)})}v(we,ht)}),v(V,ce)},R=V=>{var ce=fm(),we=d(ce);oa(we,()=>ke(n(Be).body)),v(V,ce)};E(lt,V=>{var ce,we;n(ot)&&((ce=n(Be).prevPeriod)!=null&&ce.label)&&((we=n(Be).diff)==null?void 0:we.length)>0?V(Et):V(R,-1)})}v(Ee,ue)};E(xn,Ee=>{n(Be)&&Ee(Nn)})}N((Ee,ue)=>{Le(It,1,`vw-text-section ${n(pe).status==="stale"?"vw-text-section-stale":""}`,"svelte-1l2nqwu"),Le(mt,1,`vw-status-pill ${Ee??""}`,"svelte-1l2nqwu"),P(Lt,ue)},[()=>ie(n(pe).status),()=>T(n(pe).status)]),v(at,It)}),N(()=>P(Jt,`본문 ${n(p).sectionCount??""}개`)),v(Xt,Fe)};E(Wr,Xt=>{var Fe,yr;((yr=(Fe=n(p))==null?void 0:Fe.sections)==null?void 0:yr.length)>0&&Xt(jt)})}var an=m(Wr,2);{var Gn=Xt=>{var Fe=mm();v(Xt,Fe)};E(an,Xt=>{n(Oe).length>0&&Xt(Gn)})}var sn=m(an,2);Ie(sn,17,()=>n(Oe),Te,(Xt,Fe)=>{var yr=ye(),Pn=ee(yr);{var Hn=Jt=>{const St=B(()=>{var Pe;return((Pe=n(Fe).data)==null?void 0:Pe.columns)||[]}),rr=B(()=>{var Pe;return((Pe=n(Fe).data)==null?void 0:Pe.rows)||[]}),Ht=B(()=>n(Fe).meta||{}),kr=B(()=>n(Ht).scaleDivisor||1);var Cr=_m(),Sr=ee(Cr);{var Dr=Pe=>{var Je=hm(),mt=d(Je);N(()=>P(mt,`(단위: ${n(Ht).scale??""})`)),v(Pe,Je)};E(Sr,Pe=>{n(Ht).scale&&Pe(Dr)})}var at=m(Sr,2),pe=d(at),Be=d(pe),ot=d(Be),It=d(ot);Ie(It,21,()=>n(St),Te,(Pe,Je,mt)=>{const Lt=B(()=>/^\d{4}/.test(n(Je)));var Mt=gm(),ir=d(Mt);N(()=>{Le(Mt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Lt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${mt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(ir,n(Je))}),v(Pe,Mt)});var vr=m(ot);Ie(vr,21,()=>n(rr),Te,(Pe,Je,mt)=>{var Lt=bm();Le(Lt,1,`hover:bg-white/[0.03] ${mt%2===1?"bg-white/[0.012]":""}`),Ie(Lt,21,()=>n(St),Te,(Mt,ir,Kr)=>{const lr=B(()=>n(Je)[n(ir)]??""),Tr=B(()=>oe(n(lr))),g=B(()=>ct(n(lr))),D=B(()=>n(Tr)?Bt(n(lr),n(kr)):n(lr));var de=xm(),_e=d(de);N(()=>{Le(de,1,`px-3 py-1.5 border-b border-white/[0.025]
																	${n(Tr)?"text-right tabular-nums font-mono text-[11.5px]":"whitespace-nowrap"}
																	${n(g)?"text-red-400/60":n(Tr)?"text-dl-text/90":""}
																	${Kr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]":"text-dl-text-muted"}
																	${Kr===0&&mt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(_e,n(D))}),v(Mt,de)}),v(Pe,Lt)}),v(Jt,Cr)},Un=Jt=>{const St=B(()=>{var Pe;return((Pe=n(Fe).data)==null?void 0:Pe.columns)||[]}),rr=B(()=>{var Pe;return((Pe=n(Fe).data)==null?void 0:Pe.rows)||[]}),Ht=B(()=>n(Fe).meta||{}),kr=B(()=>n(Ht).scaleDivisor||1);var Cr=Sm(),Sr=ee(Cr);{var Dr=Pe=>{var Je=wm(),mt=d(Je);N(()=>P(mt,`(단위: ${n(Ht).scale??""})`)),v(Pe,Je)};E(Sr,Pe=>{n(Ht).scale&&Pe(Dr)})}var at=m(Sr,2),pe=d(at),Be=d(pe),ot=d(Be),It=d(ot);Ie(It,21,()=>n(St),Te,(Pe,Je,mt)=>{const Lt=B(()=>/^\d{4}/.test(n(Je)));var Mt=ym(),ir=d(Mt);N(()=>{Le(Mt,1,`px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																${n(Lt)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
																${mt===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(ir,n(Je))}),v(Pe,Mt)});var vr=m(ot);Ie(vr,21,()=>n(rr),Te,(Pe,Je,mt)=>{var Lt=Cm();Le(Lt,1,`hover:bg-white/[0.03] ${mt%2===1?"bg-white/[0.012]":""}`),Ie(Lt,21,()=>n(St),Te,(Mt,ir,Kr)=>{const lr=B(()=>n(Je)[n(ir)]??""),Tr=B(()=>oe(n(lr))),g=B(()=>ct(n(lr))),D=B(()=>n(Tr)?n(kr)>1?Bt(n(lr),n(kr)):Rt(n(lr)):n(lr));var de=km(),_e=d(de);N(()=>{Le(de,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(Tr)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(g)?"text-red-400/60":n(Tr)?"text-dl-text/90":""}
																	${Kr===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Kr===0&&mt%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(_e,n(D))}),v(Mt,de)}),v(Pe,Lt)}),v(Jt,Cr)},Wn=Jt=>{const St=B(()=>Ct(Object.keys(n(Fe).rawMarkdown))),rr=B(()=>n(k).get(n(Fe).block)??0),Ht=B(()=>n(St)[n(rr)]||n(St)[0]);var kr=zm(),Cr=d(kr);{var Sr=Be=>{var ot=Am(),It=d(ot);Ie(It,17,()=>n(St).slice(0,8),Te,(Je,mt,Lt)=>{var Mt=Mm(),ir=d(Mt);N(()=>{Le(Mt,1,`px-2 py-0.5 rounded text-[10px] transition-colors
															${Lt===n(rr)?"bg-white/[0.08] text-dl-text font-medium":"text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]"}`),P(ir,n(mt))}),ae("click",Mt,()=>K(n(Fe).block,Lt)),v(Je,Mt)});var vr=m(It,2);{var Pe=Je=>{var mt=Em(),Lt=d(mt);N(()=>P(Lt,`외 ${n(St).length-8}개`)),v(Je,mt)};E(vr,Je=>{n(St).length>8&&Je(Pe)})}v(Be,ot)};E(Cr,Be=>{n(St).length>1&&Be(Sr)})}var Dr=m(Cr,2),at=d(Dr),pe=d(at);oa(pe,()=>es(n(Fe).rawMarkdown[n(Ht)])),v(Jt,kr)},or=Jt=>{const St=B(()=>{var ot;return((ot=n(Fe).data)==null?void 0:ot.columns)||[]}),rr=B(()=>{var ot;return((ot=n(Fe).data)==null?void 0:ot.rows)||[]});var Ht=Nm(),kr=d(Ht),Cr=d(kr);Li(Cr,{size:12,class:"text-emerald-400/50"});var Sr=m(kr,2),Dr=d(Sr),at=d(Dr),pe=d(at);Ie(pe,21,()=>n(St),Te,(ot,It,vr)=>{const Pe=B(()=>/^\d{4}/.test(n(It)));var Je=Tm(),mt=d(Je);N(()=>{Le(Je,1,`px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															${n(Pe)?"text-right text-dl-text-dim/70":"text-left text-dl-text"}
															${vr===0?"sticky left-0 z-[2] bg-dl-bg-card":"bg-dl-bg-card"}`),P(mt,n(It))}),v(ot,Je)});var Be=m(at);Ie(Be,21,()=>n(rr),Te,(ot,It,vr)=>{var Pe=Pm();Le(Pe,1,`hover:bg-white/[0.03] ${vr%2===1?"bg-white/[0.012]":""}`),Ie(Pe,21,()=>n(St),Te,(Je,mt,Lt)=>{const Mt=B(()=>n(It)[n(mt)]??""),ir=B(()=>oe(n(Mt))),Kr=B(()=>ct(n(Mt)));var lr=Im(),Tr=d(lr);N(g=>{Le(lr,1,`px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	${n(ir)?"text-right tabular-nums":"whitespace-pre-wrap"}
																	${n(Kr)?"text-red-400/60":n(ir)?"text-dl-text/90":""}
																	${Lt===0?"text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark":"text-dl-text-muted"}
																	${Lt===0&&vr%2===1?"!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]":""}`),P(Tr,g)},[()=>n(ir)?Rt(n(Mt)):n(Mt)]),v(Je,lr)}),v(ot,Pe)}),v(Jt,Ht)},La=Jt=>{const St=B(()=>n(Fe).data.columns),rr=B(()=>n(Fe).data.rows||[]);var Ht=Rm(),kr=d(Ht),Cr=d(kr),Sr=d(Cr),Dr=d(Sr);Ie(Dr,21,()=>n(St),Te,(pe,Be)=>{var ot=$m(),It=d(ot);N(()=>P(It,n(Be))),v(pe,ot)});var at=m(Sr);Ie(at,21,()=>n(rr),Te,(pe,Be,ot)=>{var It=Om();Le(It,1,`hover:bg-white/[0.03] ${ot%2===1?"bg-white/[0.012]":""}`),Ie(It,21,()=>n(St),Te,(vr,Pe)=>{var Je=Lm(),mt=d(Je);N(()=>P(mt,n(Be)[n(Pe)]??"")),v(vr,Je)}),v(pe,It)}),v(Jt,Ht)};E(Pn,Jt=>{var St,rr;n(Fe).kind==="finance"?Jt(Hn):n(Fe).kind==="structured"?Jt(Un,1):n(Fe).kind==="raw_markdown"&&n(Fe).rawMarkdown?Jt(Wn,2):n(Fe).kind==="report"?Jt(or,3):((rr=(St=n(Fe).data)==null?void 0:St.columns)==null?void 0:rr.length)>0&&Jt(La,4)})}v(Xt,yr)}),v(De,bt)};E(ut,De=>{n(b)?De(nt):De(xt,-1)})}N(De=>{P(We,De),qn(Ke,"title",n(I)?"목차 표시":"전체화면")},[()=>q(n(l))]),ae("click",Ke,()=>u(I,!n(I))),v(rt,Yt)};E(ze,rt=>{n(l)?rt(wr,-1):rt(Re)})}v(w,j)},Tt=w=>{var j=qm(),O=d(j);jn(O,{size:36,strokeWidth:1,class:"opacity-20"}),v(w,j)};E(fr,w=>{var j;n(o)?w(Dt):(j=n(s))!=null&&j.rows?w(vt,1):w(Tt,-1)})}v(e,gt),nn()}Bn(["click"]);var Gm=h('<span class="text-[12px] font-semibold text-dl-text truncate"> </span> <span class="text-[10px] font-mono text-dl-text-dim"> </span>',1),Hm=h('<span class="text-[12px] font-semibold text-dl-text"> </span>'),Um=h('<span class="text-[12px] font-semibold text-dl-text">데이터</span>'),Wm=h('<button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" title="Excel 다운로드"><!></button> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button>',1),Km=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Ym=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed"> </pre>'),Xm=h('<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2"> </div>'),Jm=h('<div class="prose-dartlab text-[13px] leading-[1.7]"><!></div>'),Qm=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),Zm=h("<!> <!>",1),eh=h('<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40"> </pre>'),th=h('<div class="p-4"><!></div>'),rh=h('<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">표시할 내용이 없습니다</div>'),nh=h('<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark"><div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0"><div class="flex items-center gap-2 min-w-0"><!></div> <div class="flex items-center gap-1"><!> <button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div></div> <div class="flex-1 overflow-auto min-h-0"><!></div></div>');function ah(e,t){rn(t,!0);let r=dt(t,"mode",3,null),a=dt(t,"company",3,null),s=dt(t,"data",3,null),o=dt(t,"onTopicChange",3,null),i=dt(t,"onFullscreen",3,null),l=dt(t,"isFullscreen",3,!1),c=G(!1);async function f(){var T;if(!(!((T=a())!=null&&T.stockCode)||n(c))){u(c,!0);try{await Bu(a().stockCode)}catch(ie){console.error("Excel download error:",ie)}u(c,!1)}}function p(T){return T?/^\|.+\|$/m.test(T)||/^#{1,3} /m.test(T)||/\*\*[^*]+\*\*/m.test(T)||/```/.test(T):!1}var b=nh(),_=d(b),z=d(_),y=d(z);{var I=T=>{var ie=Gm(),fe=ee(ie),be=d(fe),ve=m(fe,2),Ae=d(ve);N(()=>{P(be,a().corpName||a().company),P(Ae,a().stockCode)}),v(T,ie)},k=T=>{var ie=Hm(),fe=d(ie);N(()=>P(fe,s().label)),v(T,ie)},C=T=>{var ie=Um();v(T,ie)};E(y,T=>{var ie;r()==="viewer"&&a()?T(I):r()==="data"&&((ie=s())!=null&&ie.label)?T(k,1):r()==="data"&&T(C,2)})}var L=m(z,2),U=d(L);{var S=T=>{var ie=Wm(),fe=ee(ie),be=d(fe);{var ve=ke=>{vn(ke,{size:14,class:"animate-spin"})},Ae=ke=>{ws(ke,{size:14})};E(be,ke=>{n(c)?ke(ve):ke(Ae,-1)})}var me=m(fe,2),he=d(me);{var W=ke=>{id(ke,{size:14})},tt=ke=>{od(ke,{size:14})};E(he,ke=>{l()?ke(W):ke(tt,-1)})}N(()=>{fe.disabled=n(c),qn(me,"title",l()?"패널 모드로":"전체 화면")}),ae("click",fe,f),ae("click",me,()=>{var ke;return(ke=i())==null?void 0:ke()}),v(T,ie)};E(U,T=>{var ie;r()==="viewer"&&((ie=a())!=null&&ie.stockCode)&&T(S)})}var q=m(U,2),le=d(q);Bs(le,{size:15});var $=m(_,2),x=d($);{var H=T=>{Bm(T,{get stockCode(){return a().stockCode},get onTopicChange(){return o()}})},te=T=>{var ie=th(),fe=d(ie);{var be=me=>{var he=ye(),W=ee(he);{var tt=re=>{var Y=Km(),X=d(Y);oa(X,()=>es(s())),v(re,Y)},ke=B(()=>p(s())),A=re=>{var Y=Ym(),X=d(Y);N(()=>P(X,s())),v(re,Y)};E(W,re=>{n(ke)?re(tt):re(A,-1)})}v(me,he)},ve=me=>{var he=Zm(),W=ee(he);{var tt=X=>{var ge=Xm(),Z=d(ge);N(()=>P(Z,s().module)),v(X,ge)};E(W,X=>{s().module&&X(tt)})}var ke=m(W,2);{var A=X=>{var ge=Jm(),Z=d(ge);oa(Z,()=>es(s().text)),v(X,ge)},re=B(()=>p(s().text)),Y=X=>{var ge=Qm(),Z=d(ge);N(()=>P(Z,s().text)),v(X,ge)};E(ke,X=>{n(re)?X(A):X(Y,-1)})}v(me,he)},Ae=me=>{var he=eh(),W=d(he);N(tt=>P(W,tt),[()=>JSON.stringify(s(),null,2)]),v(me,he)};E(fe,me=>{var he;typeof s()=="string"?me(be):(he=s())!=null&&he.text?me(ve,1):me(Ae,-1)})}v(T,ie)},K=T=>{var ie=rh();v(T,ie)};E(x,T=>{r()==="viewer"&&a()?T(H):r()==="data"&&s()?T(te,1):T(K,-1)})}ae("click",q,()=>{var T;return(T=t.onClose)==null?void 0:T.call(t)}),v(e,b),nn()}Bn(["click"]);var sh=h('<button class="sidebar-overlay" aria-label="사이드바 닫기"></button>'),oh=h("<!> <span>확인 중...</span>",1),ih=h("<!> <span>설정 필요</span>",1),lh=h('<span class="text-dl-text-dim">/</span> <span class="max-w-[80px] truncate"> </span>',1),dh=h('<span class="w-1.5 h-1.5 rounded-full bg-dl-success"></span> <span> </span> <!>',1),ch=h('<div class="flex-shrink-0 border-l border-dl-border/30 transition-all duration-300"><!></div>'),uh=h('<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>'),fh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),vh=h('<!> <span class="text-[10px] text-amber-400">인증 필요</span>',1),ph=h('<!> <span class="text-[10px] text-dl-text-dim">미설치</span>',1),mh=h('<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light"><!> API 키가 유효하지 않습니다. 다시 확인해주세요.</div>'),hh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[11px] text-dl-text-muted mb-2"> </div> <div class="flex items-center gap-2"><input type="password" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 인증</button></div> <!></div>'),gh=h('<button class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"><!></button>'),xh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">인증됨</span> <span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span></div> <div class="flex items-center gap-2 mt-2"><input type="password" placeholder="새 API 키 (변경 시에만)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <!></div></div>'),bh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div> <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"><!> Ollama 다운로드 (ollama.com) <!></a> <div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div></div>'),_h=h('<div class="px-4 pb-3 border-t border-dl-border/50 pt-3"><div class="flex items-center gap-2 text-[12px] text-amber-400"><!> Ollama가 설치되었지만 실행되지 않고 있습니다</div> <div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div></div>'),wh=h('<div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">npm install -g @openai/codex</div></div></div>'),yh=h('<div class="text-[10px] text-dl-text-dim mt-2"> </div>'),kh=h('<div class="text-[12px] text-dl-text mb-2.5"> </div> <div class="space-y-2"><!> <div class="flex items-start gap-2.5"><span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0"> </span> <div class="flex-1"><div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div> <div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">codex login</div></div></div></div> <!> <div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20"><!> <span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span></div>',1),Ch=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><!> <div class="text-[10px] text-dl-text-dim mt-2"> </div></div>'),Sh=h('<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5"><div class="flex items-center justify-between"><div class="flex items-center gap-2"><!> <span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span></div> <button class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"><!> 로그아웃</button></div></div>'),Mh=h('<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim"><!> 모델 목록 불러오는 중...</div>'),Eh=h("<button> <!></button>"),Ah=h('<div class="flex flex-wrap gap-1.5"></div>'),zh=h('<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>'),Th=h('<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker"><div class="flex items-center justify-between mb-1.5"><span class="text-[11px] text-dl-text flex items-center gap-1.5"><!> 다운로드 중</span> <button class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">취소</button></div> <div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"></div></div> <div class="text-[10px] text-dl-text-dim mt-1"> </div></div>'),Ih=h('<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light"> </span>'),Ph=h('<button class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"><div class="flex-1 min-w-0"><div class="flex items-center gap-1.5"><span class="text-[11px] font-medium text-dl-text"> </span> <span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim"> </span> <!></div> <div class="text-[10px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-1.5 flex-shrink-0"><span class="text-[9px] text-dl-text-dim"> </span> <!></div></button>'),Nh=h('<div class="flex items-center gap-1.5"><input type="text" placeholder="모델명 (예: gemma3)" class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"/> <button class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"><!> 받기</button></div> <div class="mt-2.5 space-y-1"></div>',1),$h=h('<div class="mt-3 pt-3 border-t border-dl-border/30"><div class="flex items-center justify-between mb-2"><span class="text-[11px] text-dl-text-muted">모델 다운로드</span> <a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors">전체 목록 <!></a></div> <!></div>'),Lh=h('<div class="px-4 pb-4 border-t border-dl-border/50 pt-3"><div class="flex items-center justify-between mb-2.5"><span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span> <!></div> <!> <!></div>'),Oh=h("<!> <!> <!> <!> <!> <!>",1),Rh=h('<div><button class="flex items-center gap-3 w-full px-4 py-3 text-left"><span></span> <div class="flex-1 min-w-0"><div class="flex items-center gap-2"><span class="text-[13px] font-medium text-dl-text"> </span> <!></div> <div class="text-[11px] text-dl-text-dim mt-0.5"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><!></div></button> <!></div>'),Dh=h('<div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden" role="dialog" aria-modal="true" aria-labelledby="settings-dialog-title" tabindex="-1"><div class="border-b border-dl-border/40 px-6 pt-5 pb-3"><div class="flex items-center justify-between"><div><div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div> <div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div></div> <button class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" aria-label="설정 닫기"><!></button></div></div> <div class="px-6 pb-5 max-h-[70vh] overflow-y-auto"><div class="space-y-2.5"></div></div> <div class="flex items-center justify-between px-6 py-3 border-t border-dl-border"><div class="text-[10px] text-dl-text-dim"><!></div> <button class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">닫기</button></div></div></div>'),jh=h('<div class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn" role="presentation"><div class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" tabindex="-1"><div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div> <div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div> <div class="flex items-center justify-end gap-2"><button class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors">취소</button> <button class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors">삭제</button></div></div></div>'),Vh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div> <div class="flex items-center gap-2 flex-shrink-0"><span class="text-[10px] text-dl-text-dim">공시 보기</span> <!></div></button>'),qh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">검색 결과</div></div> <!>',1),Fh=h('<button><div class="w-8 h-8 rounded-lg bg-dl-bg-darker border border-dl-border/40 flex items-center justify-center text-[11px] font-semibold text-dl-text-muted flex-shrink-0"> </div> <div class="flex-1 min-w-0"><div class="text-[14px] font-medium text-dl-text truncate"> </div> <div class="text-[11px] text-dl-text-dim"> </div></div></button>'),Bh=h('<div class="px-3 pt-2 pb-1"><div class="text-[10px] uppercase tracking-wider text-dl-text-dim px-2 mb-1">최근 조회</div></div> <!>',1),Gh=h('<div class="flex items-center justify-center py-8 text-[13px] text-dl-text-dim">검색 결과가 없습니다</div>'),Hh=h('<div class="flex flex-col items-center justify-center py-10 text-dl-text-dim"><!> <div class="text-[13px]">종목명 또는 종목코드를 입력하세요</div> <div class="text-[11px] mt-1 opacity-60">검색 후 공시를 볼 수 있습니다</div></div>'),Uh=h('<div class="fixed inset-0 z-[200] flex items-start justify-center pt-[12vh] bg-black/70 backdrop-blur-md animate-fadeIn" role="presentation"><div class="w-full max-w-2xl mx-4 bg-dl-bg-card border border-dl-border/60 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden"><div class="flex items-center gap-3 px-5 py-4 border-b border-dl-border/40"><!> <input type="text" placeholder="종목명 또는 종목코드 검색..." class="flex-1 bg-transparent border-none outline-none text-[16px] text-dl-text placeholder:text-dl-text-dim"/> <kbd class="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-dl-text-dim border border-dl-border/60 bg-dl-bg-darker">ESC</kbd></div> <div class="max-h-[50vh] overflow-y-auto"><!></div> <div class="flex items-center gap-4 px-5 py-2.5 border-t border-dl-border/30 text-[10px] text-dl-text-dim"><span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">↑↓</kbd> 이동</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">Enter</kbd> 선택</span> <span class="flex items-center gap-1"><kbd class="px-1 py-px rounded border border-dl-border/40 bg-dl-bg-darker font-mono">ESC</kbd> 닫기</span></div></div></div>'),Wh=h('<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true"><div><div class="min-w-0 flex-1"> </div> <button class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current" aria-label="알림 닫기"><!></button></div></div>'),Kh=h('<div class="flex h-screen bg-dl-bg-dark overflow-hidden"><!> <div><!></div> <div class="relative flex flex-col flex-1 min-w-0 min-h-0 glow-bg"><div class="absolute top-2 left-3 z-20 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"><!></button></div> <div class="absolute top-2 right-3 z-20 flex items-center gap-1 pointer-events-auto"><button class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="종목 검색 (Ctrl+K)"><!></button> <a href="https://eddmpython.github.io/dartlab/" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="Documentation"><!></a> <a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5 transition-colors" title="GitHub"><!></a> <a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener noreferrer" class="p-1.5 rounded-lg text-[#ffdd00]/60 hover:text-[#ffdd00] hover:bg-white/5 transition-colors" title="Buy me a coffee"><!></a> <button><!> <!></button></div> <div class="flex flex-1 min-h-0"><div class="min-w-0 flex-1 flex flex-col"><!></div> <!></div></div></div>  <!> <!> <!> <!>',1);function Yh(e,t){rn(t,!0);let r=G(""),a=G(!1),s=G(null),o=G(qt({})),i=G(qt({})),l=G(null),c=G(null),f=G(qt([])),p=G(!1),b=G(0),_=G(!0),z=G(""),y=G(!1),I=G(null),k=G(qt({})),C=G(qt({})),L=G(""),U=G(!1),S=G(null),q=G(""),le=G(!1),$=G(""),x=G(0),H=G(null),te=G(null),K=G(null);const T=Gf();let ie=G(!1),fe=B(()=>n(ie)?"100%":T.panelMode==="viewer"?"65%":"50%"),be=G(!1),ve=G(""),Ae=G(qt([])),me=G(-1),he=null,W=G(null),tt=G(!1);function ke(){u(tt,window.innerWidth<=768),n(tt)&&(u(p,!1),T.closePanel())}Dn(()=>(ke(),window.addEventListener("resize",ke),()=>window.removeEventListener("resize",ke))),Dn(()=>{!n(y)||!n(te)||requestAnimationFrame(()=>{var g;return(g=n(te))==null?void 0:g.focus()})}),Dn(()=>{!n(A)||!n(K)||requestAnimationFrame(()=>{var g;return(g=n(K))==null?void 0:g.focus()})}),Dn(()=>{!n(be)||!n(W)||requestAnimationFrame(()=>{var g;return(g=n(W))==null?void 0:g.focus()})});let A=G(null),re=G(""),Y=G("error"),X=G(!1);function ge(g,D="error",de=4e3){u(re,g,!0),u(Y,D,!0),u(X,!0),setTimeout(()=>{u(X,!1)},de)}const Z=Vf();Dn(()=>{Ct()});let oe=G(qt({}));function ct(g){return g==="chatgpt"?"codex":g}function Bt(g){return`dartlab-api-key:${ct(g)}`}function Rt(g){return typeof sessionStorage>"u"||!g?"":sessionStorage.getItem(Bt(g))||""}function wt(g,D){typeof sessionStorage>"u"||!g||(D?sessionStorage.setItem(Bt(g),D):sessionStorage.removeItem(Bt(g)))}async function er(g,D=null,de=null){var Me;const _e=await ju(g,D,de);if(_e!=null&&_e.provider){const $e=ct(_e.provider);u(o,{...n(o),[$e]:{...n(o)[$e]||{},available:!!_e.available,model:_e.model||((Me=n(o)[$e])==null?void 0:Me.model)||D||null}},!0)}return _e}async function Ct(){var g,D,de;u(_,!0);try{const _e=await Du();u(o,_e.providers||{},!0),u(i,_e.ollama||{},!0),u(oe,_e.codex||{},!0),_e.version&&u(z,_e.version,!0);const Me=ct(localStorage.getItem("dartlab-provider")),$e=localStorage.getItem("dartlab-model"),st=Rt(Me);if(Me&&((g=n(o)[Me])!=null&&g.available)){u(l,Me,!0),u(I,Me,!0),u(L,st,!0),await Oe(Me);const it=n(k)[Me]||[];$e&&it.includes($e)?u(c,$e,!0):it.length>0&&(u(c,it[0],!0),localStorage.setItem("dartlab-model",n(c))),u(f,it,!0),u(_,!1);return}if(Me&&n(o)[Me]){if(u(l,Me,!0),u(I,Me,!0),u(L,st,!0),st)try{await er(Me,$e,st)}catch{}await Oe(Me);const it=n(k)[Me]||[];u(f,it,!0),$e&&it.includes($e)?u(c,$e,!0):it.length>0&&u(c,it[0],!0),u(_,!1);return}for(const it of["codex","ollama","openai"])if((D=n(o)[it])!=null&&D.available){u(l,it,!0),u(I,it,!0),u(L,Rt(it),!0),await Oe(it);const Ut=n(k)[it]||[];u(f,Ut,!0),u(c,((de=n(o)[it])==null?void 0:de.model)||(Ut.length>0?Ut[0]:null),!0),n(c)&&localStorage.setItem("dartlab-model",n(c));break}}catch{}u(_,!1)}async function Oe(g){g=ct(g),u(C,{...n(C),[g]:!0},!0);try{const D=await Vu(g);u(k,{...n(k),[g]:D.models||[]},!0)}catch{u(k,{...n(k),[g]:[]},!0)}u(C,{...n(C),[g]:!1},!0)}async function gt(g){var de;g=ct(g),u(l,g,!0),u(c,null),u(I,g,!0),localStorage.setItem("dartlab-provider",g),localStorage.removeItem("dartlab-model"),u(L,Rt(g),!0),u(S,null),await Oe(g);const D=n(k)[g]||[];if(u(f,D,!0),D.length>0&&(u(c,((de=n(o)[g])==null?void 0:de.model)||D[0],!0),localStorage.setItem("dartlab-model",n(c)),n(L)))try{await er(g,n(c),n(L))}catch{}}async function fr(g){u(c,g,!0),localStorage.setItem("dartlab-model",g);const D=Rt(n(l));if(D)try{await er(ct(n(l)),g,D)}catch{}}function Dt(g){g=ct(g),n(I)===g?u(I,null):(u(I,g,!0),Oe(g))}async function vt(){const g=n(L).trim();if(!(!g||!n(l))){u(U,!0),u(S,null);try{const D=await er(ct(n(l)),n(c),g);D.available?(wt(n(l),g),u(S,"success"),!n(c)&&D.model&&u(c,D.model,!0),await Oe(n(l)),u(f,n(k)[n(l)]||[],!0),ge("API 키 인증 성공","success")):(wt(n(l),""),u(S,"error"))}catch{wt(n(l),""),u(S,"error")}u(U,!1)}}async function Tt(){try{await Fu(),n(l)==="codex"&&u(o,{...n(o),codex:{...n(o).codex,available:!1}},!0),ge("Codex 계정 로그아웃 완료","success"),await Ct()}catch{ge("로그아웃 실패")}}function w(){const g=n(q).trim();!g||n(le)||(u(le,!0),u($,"준비 중..."),u(x,0),u(H,qu(g,{onProgress(D){D.total&&D.completed!==void 0?(u(x,Math.round(D.completed/D.total*100),!0),u($,`다운로드 중... ${n(x)}%`)):D.status&&u($,D.status,!0)},async onDone(){u(le,!1),u(H,null),u(q,""),u($,""),u(x,0),ge(`${g} 다운로드 완료`,"success"),await Oe("ollama"),u(f,n(k).ollama||[],!0),n(f).includes(g)&&await fr(g)},onError(D){u(le,!1),u(H,null),u($,""),u(x,0),ge(`다운로드 실패: ${D}`)}}),!0))}function j(){n(H)&&(n(H).abort(),u(H,null)),u(le,!1),u(q,""),u($,""),u(x,0)}function O(){u(p,!n(p))}function J(g){T.openData(g)}function F(g,D=null){T.openEvidence(g,D)}function ze(g){T.openViewer(g)}function Re(){if(u(L,""),u(S,null),n(l))u(I,n(l),!0);else{const g=Object.keys(n(o));u(I,g.length>0?g[0]:null,!0)}u(y,!0),n(I)&&Oe(n(I))}function wr(g){var D,de,_e,Me;if(g)for(let $e=g.messages.length-1;$e>=0;$e--){const st=g.messages[$e];if(st.role==="assistant"&&((D=st.meta)!=null&&D.stockCode||(de=st.meta)!=null&&de.company||st.company)){T.syncCompanyFromMessage({company:((_e=st.meta)==null?void 0:_e.company)||st.company,stockCode:(Me=st.meta)==null?void 0:Me.stockCode},T.selectedCompany);return}}}function rt(){Z.createConversation(),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function Yt(g){Z.setActive(g),wr(Z.active),u(r,""),u(a,!1),n(s)&&(n(s).abort(),u(s,null))}function tr(g){u(A,g,!0)}function Ur(){n(A)&&(Z.deleteConversation(n(A)),u(A,null))}function Ne(){var D;const g=Z.active;if(!g)return null;for(let de=g.messages.length-1;de>=0;de--){const _e=g.messages[de];if(_e.role==="assistant"&&((D=_e.meta)!=null&&D.stockCode))return _e.meta.stockCode}return null}async function Ce(g=null){var ue,lt,Et;const D=(g??n(r)).trim();if(!D||n(a))return;if(!n(l)||!((ue=n(o)[n(l)])!=null&&ue.available)){ge("먼저 AI Provider를 설정해주세요. 우상단 설정 버튼을 클릭하세요."),Re();return}Z.activeId||Z.createConversation();const de=Z.activeId;Z.addMessage("user",D),u(r,""),u(a,!0),Z.addMessage("assistant",""),Z.updateLastMessage({loading:!0,startedAt:Date.now()}),xs(b);const _e=Z.active,Me=[];let $e=null;if(_e){const R=_e.messages.slice(0,-2);for(const V of R)if((V.role==="user"||V.role==="assistant")&&V.text&&V.text.trim()&&!V.error&&!V.loading){const ce={role:V.role,text:V.text};V.role==="assistant"&&((lt=V.meta)!=null&&lt.stockCode)&&(ce.meta={company:V.meta.company||V.company,stockCode:V.meta.stockCode,modules:V.meta.includedModules||null,market:V.meta.market||null,topic:V.meta.topic||null,topicLabel:V.meta.topicLabel||null,dialogueMode:V.meta.dialogueMode||null,questionTypes:V.meta.questionTypes||null,userGoal:V.meta.userGoal||null},$e=V.meta.stockCode),Me.push(ce)}}const st=((Et=T.selectedCompany)==null?void 0:Et.stockCode)||$e||Ne(),it=T.getViewContext();function Ut(){return Z.activeId!==de}const xn={provider:n(l),model:n(c),viewContext:it},Nn=Rt(n(l));Nn&&(xn.api_key=Nn);const Ee=Uu(st,D,xn,{onMeta(R){var ht;if(Ut())return;const V=Z.active,ce=V==null?void 0:V.messages[V.messages.length-1],xe={meta:{...(ce==null?void 0:ce.meta)||{},...R}};R.company&&(xe.company=R.company,Z.activeId&&((ht=Z.active)==null?void 0:ht.title)==="새 대화"&&Z.updateTitle(Z.activeId,R.company)),R.stockCode&&(xe.stockCode=R.stockCode),(R.company||R.stockCode)&&T.syncCompanyFromMessage(R,T.selectedCompany),Z.updateLastMessage(xe)},onSnapshot(R){Ut()||Z.updateLastMessage({snapshot:R})},onContext(R){if(Ut())return;const V=Z.active;if(!V)return;const ce=V.messages[V.messages.length-1],we=(ce==null?void 0:ce.contexts)||[];Z.updateLastMessage({contexts:[...we,{module:R.module,label:R.label,text:R.text}]})},onSystemPrompt(R){Ut()||Z.updateLastMessage({systemPrompt:R.text,userContent:R.userContent||null})},onToolCall(R){if(Ut())return;const V=Z.active;if(!V)return;const ce=V.messages[V.messages.length-1],we=(ce==null?void 0:ce.toolEvents)||[];Z.updateLastMessage({toolEvents:[...we,{type:"call",name:R.name,arguments:R.arguments}]})},onToolResult(R){if(Ut())return;const V=Z.active;if(!V)return;const ce=V.messages[V.messages.length-1],we=(ce==null?void 0:ce.toolEvents)||[];Z.updateLastMessage({toolEvents:[...we,{type:"result",name:R.name,result:R.result}]})},onChunk(R){if(Ut())return;const V=Z.active;if(!V)return;const ce=V.messages[V.messages.length-1];Z.updateLastMessage({text:((ce==null?void 0:ce.text)||"")+R}),xs(b)},onDone(){if(Ut())return;const R=Z.active,V=R==null?void 0:R.messages[R.messages.length-1],ce=V!=null&&V.startedAt?((Date.now()-V.startedAt)/1e3).toFixed(1):null;Z.updateLastMessage({loading:!1,duration:ce}),Z.flush(),u(a,!1),u(s,null),xs(b)},onError(R,V,ce){Ut()||(Z.updateLastMessage({text:`오류: ${R}`,loading:!1,error:!0}),Z.flush(),V==="login"?(ge(`${R} — 설정에서 Codex 로그인을 확인하세요`),Re()):V==="install"?(ge(`${R} — 설정에서 Codex 설치 안내를 확인하세요`),Re()):ge(R),u(a,!1),u(s,null))}},Me);u(s,Ee,!0)}function pt(){n(s)&&(n(s).abort(),u(s,null),u(a,!1),Z.updateLastMessage({loading:!1}),Z.flush())}function Se(){const g=Z.active;if(!g||g.messages.length<2)return;let D="";for(let de=g.messages.length-1;de>=0;de--)if(g.messages[de].role==="user"){D=g.messages[de].text;break}D&&(Z.removeLastMessage(),Z.removeLastMessage(),u(r,D,!0),requestAnimationFrame(()=>{Ce()}))}function We(){const g=Z.active;if(!g)return;let D=`# ${g.title}

`;for(const $e of g.messages)$e.role==="user"?D+=`## You

${$e.text}

`:$e.role==="assistant"&&$e.text&&(D+=`## DartLab

${$e.text}

`);const de=new Blob([D],{type:"text/markdown;charset=utf-8"}),_e=URL.createObjectURL(de),Me=document.createElement("a");Me.href=_e,Me.download=`${g.title||"dartlab-chat"}.md`,Me.click(),URL.revokeObjectURL(_e),ge("대화가 마크다운으로 내보내졌습니다","success")}function Ke(){u(be,!0),u(ve,""),u(Ae,[],!0),u(me,-1)}function yt(g){(g.metaKey||g.ctrlKey)&&g.key==="n"&&(g.preventDefault(),rt()),(g.metaKey||g.ctrlKey)&&g.key==="k"&&(g.preventDefault(),Ke()),(g.metaKey||g.ctrlKey)&&g.shiftKey&&g.key==="S"&&(g.preventDefault(),O()),g.key==="Escape"&&n(be)?u(be,!1):g.key==="Escape"&&n(y)?u(y,!1):g.key==="Escape"&&n(A)?u(A,null):g.key==="Escape"&&T.panelOpen&&T.closePanel()}let Q=B(()=>{var g;return((g=Z.active)==null?void 0:g.messages)||[]}),qe=B(()=>Z.active&&Z.active.messages.length>0),ut=B(()=>{var g;return!n(_)&&(!n(l)||!((g=n(o)[n(l)])!=null&&g.available))});const nt=[{name:"gemma3",size:"3B",gb:"2.3",desc:"Google, 빠르고 가벼움",tag:"추천"},{name:"gemma3:12b",size:"12B",gb:"8.1",desc:"Google, 균형잡힌 성능"},{name:"llama3.1",size:"8B",gb:"4.7",desc:"Meta, 범용 최강",tag:"추천"},{name:"qwen2.5",size:"7B",gb:"4.7",desc:"Alibaba, 한국어 우수"},{name:"qwen2.5:14b",size:"14B",gb:"9.0",desc:"Alibaba, 한국어 최고 수준"},{name:"deepseek-r1",size:"7B",gb:"4.7",desc:"추론 특화, 분석에 적합"},{name:"phi4",size:"14B",gb:"9.1",desc:"Microsoft, 수학/코드 강점"},{name:"mistral",size:"7B",gb:"4.1",desc:"Mistral AI, 가볍고 빠름"},{name:"exaone3.5",size:"8B",gb:"4.9",desc:"LG AI, 한국어 특화",tag:"한국어"}];var xt=Kh();Va("keydown",So,yt);var De=ee(xt),bt=d(De);{var $t=g=>{var D=sh();ae("click",D,()=>{u(p,!1)}),v(g,D)};E(bt,g=>{n(tt)&&n(p)&&g($t)})}var Gt=m(bt,2),Wr=d(Gt);{let g=B(()=>n(tt)?!0:n(p));Mv(Wr,{get conversations(){return Z.conversations},get activeId(){return Z.activeId},get open(){return n(g)},get version(){return n(z)},onNewChat:()=>{rt(),n(tt)&&u(p,!1)},onSelect:D=>{Yt(D),n(tt)&&u(p,!1)},onDelete:tr,onOpenSearch:Ke})}var jt=m(Gt,2),an=d(jt),Gn=d(an),sn=d(Gn);{var Xt=g=>{cv(g,{size:18})},Fe=g=>{dv(g,{size:18})};E(sn,g=>{n(p)?g(Xt):g(Fe,-1)})}var yr=m(an,2),Pn=d(yr),Hn=d(Pn);ys(Hn,{size:14});var Un=m(Pn,2),Wn=d(Un);jn(Wn,{size:14});var or=m(Un,2),La=d(or);iv(La,{size:14});var Jt=m(or,2),St=d(Jt);sv(St,{size:14});var rr=m(Jt,2),Ht=d(rr);{var kr=g=>{var D=oh(),de=ee(D);vn(de,{size:12,class:"animate-spin"}),v(g,D)},Cr=g=>{var D=ih(),de=ee(D);vs(de,{size:12}),v(g,D)},Sr=g=>{var D=dh(),de=m(ee(D),2),_e=d(de),Me=m(de,2);{var $e=st=>{var it=lh(),Ut=m(ee(it),2),xn=d(Ut);N(()=>P(xn,n(c))),v(st,it)};E(Me,st=>{n(c)&&st($e)})}N(()=>P(_e,n(l))),v(g,D)};E(Ht,g=>{n(_)?g(kr):n(ut)?g(Cr,1):g(Sr,-1)})}var Dr=m(Ht,2);fv(Dr,{size:12});var at=m(yr,2),pe=d(at),Be=d(pe);{var ot=g=>{Tp(g,{get messages(){return n(Q)},get isLoading(){return n(a)},get scrollTrigger(){return n(b)},get selectedCompany(){return T.selectedCompany},onSend:Ce,onStop:pt,onRegenerate:Se,onExport:We,onOpenData:J,onOpenEvidence:F,onCompanySelect:ze,get inputText(){return n(r)},set inputText(D){u(r,D,!0)}})},It=g=>{Lv(g,{onSend:Ce,onCompanySelect:ze,get inputText(){return n(r)},set inputText(D){u(r,D,!0)}})};E(Be,g=>{n(qe)?g(ot):g(It,-1)})}var vr=m(pe,2);{var Pe=g=>{var D=ch(),de=d(D);ah(de,{get mode(){return T.panelMode},get company(){return T.selectedCompany},get data(){return T.panelData},onClose:()=>{u(ie,!1),T.closePanel()},onTopicChange:(_e,Me)=>T.setViewerTopic(_e,Me),onFullscreen:()=>{u(ie,!n(ie))},get isFullscreen(){return n(ie)}}),N(()=>Io(D,`width: ${n(fe)??""}; min-width: 360px; ${n(ie)?"":"max-width: 75vw;"}`)),v(g,D)};E(vr,g=>{!n(tt)&&T.panelOpen&&g(Pe)})}var Je=m(De,2);{var mt=g=>{var D=Dh(),de=d(D),_e=d(de),Me=d(_e),$e=m(d(Me),2),st=d($e);Bs(st,{size:18});var it=m(_e,2),Ut=d(it);Ie(Ut,21,()=>Object.entries(n(o)),Te,(R,V)=>{var ce=B(()=>Ui(n(V),2));let we=()=>n(ce)[0],xe=()=>n(ce)[1];const ht=B(()=>we()===n(l)),kt=B(()=>n(I)===we()),dr=B(()=>xe().auth==="api_key"),_t=B(()=>xe().auth==="cli"),Qt=B(()=>n(k)[we()]||[]),Wt=B(()=>n(C)[we()]);var At=Rh(),Vt=d(At),Ir=d(Vt),Oa=m(Ir,2),Ra=d(Oa),Is=d(Ra),Qs=d(Is),dd=m(Is,2);{var cd=Ft=>{var Er=uh();v(Ft,Er)};E(dd,Ft=>{n(ht)&&Ft(cd)})}var ud=m(Ra,2),fd=d(ud),vd=m(Oa,2),pd=d(vd);{var md=Ft=>{_s(Ft,{size:16,class:"text-dl-success"})},hd=Ft=>{var Er=fh(),Kn=ee(Er);Ri(Kn,{size:14,class:"text-amber-400"}),v(Ft,Er)},gd=Ft=>{var Er=vh(),Kn=ee(Er);vs(Kn,{size:14,class:"text-amber-400"}),v(Ft,Er)},xd=Ft=>{var Er=ph(),Kn=ee(Er);pv(Kn,{size:14,class:"text-dl-text-dim"}),v(Ft,Er)};E(pd,Ft=>{xe().available?Ft(md):n(dr)?Ft(hd,1):n(_t)&&we()==="codex"&&n(oe).installed?Ft(gd,2):n(_t)&&!xe().available&&Ft(xd,3)})}var bd=m(Vt,2);{var _d=Ft=>{var Er=Oh(),Kn=ee(Er);{var wd=zt=>{var Zt=hh(),pr=d(Zt),Ar=d(pr),Yr=m(pr,2),Mr=d(Yr),jr=m(Mr,2),Yn=d(jr);{var Xn=ft=>{vn(ft,{size:12,class:"animate-spin"})},Vr=ft=>{Ri(ft,{size:12})};E(Yn,ft=>{n(U)?ft(Xn):ft(Vr,-1)})}var on=m(Yr,2);{var Ot=ft=>{var qr=mh(),mr=d(qr);vs(mr,{size:12}),v(ft,qr)};E(on,ft=>{n(S)==="error"&&ft(Ot)})}N(ft=>{P(Ar,xe().envKey?`환경변수 ${xe().envKey}로도 설정 가능합니다`:"API 키를 입력하세요"),qn(Mr,"placeholder",we()==="openai"?"sk-...":we()==="claude"?"sk-ant-...":"API Key"),jr.disabled=ft},[()=>!n(L).trim()||n(U)]),ae("keydown",Mr,ft=>{ft.key==="Enter"&&vt()}),ja(Mr,()=>n(L),ft=>u(L,ft)),ae("click",jr,vt),v(zt,Zt)};E(Kn,zt=>{n(dr)&&!xe().available&&zt(wd)})}var Qo=m(Kn,2);{var yd=zt=>{var Zt=xh(),pr=d(Zt),Ar=d(pr);_s(Ar,{size:13,class:"text-dl-success"});var Yr=m(pr,2),Mr=d(Yr),jr=m(Mr,2);{var Yn=Vr=>{var on=gh(),Ot=d(on);{var ft=mr=>{vn(mr,{size:10,class:"animate-spin"})},qr=mr=>{var bn=ta("변경");v(mr,bn)};E(Ot,mr=>{n(U)?mr(ft):mr(qr,-1)})}N(()=>on.disabled=n(U)),ae("click",on,vt),v(Vr,on)},Xn=B(()=>n(L).trim());E(jr,Vr=>{n(Xn)&&Vr(Yn)})}ae("keydown",Mr,Vr=>{Vr.key==="Enter"&&vt()}),ja(Mr,()=>n(L),Vr=>u(L,Vr)),v(zt,Zt)};E(Qo,zt=>{n(dr)&&xe().available&&zt(yd)})}var Zo=m(Qo,2);{var kd=zt=>{var Zt=bh(),pr=m(d(Zt),2),Ar=d(pr);ws(Ar,{size:14});var Yr=m(Ar,2);Oi(Yr,{size:10,class:"ml-auto"}),v(zt,Zt)},Cd=zt=>{var Zt=_h(),pr=d(Zt),Ar=d(pr);vs(Ar,{size:14}),v(zt,Zt)};E(Zo,zt=>{we()==="ollama"&&!n(i).installed?zt(kd):we()==="ollama"&&n(i).installed&&!n(i).running&&zt(Cd,1)})}var ei=m(Zo,2);{var Sd=zt=>{var Zt=Ch(),pr=d(Zt);{var Ar=jr=>{var Yn=kh(),Xn=ee(Yn),Vr=d(Xn),on=m(Xn,2),Ot=d(on);{var ft=Fr=>{var _n=wh();v(Fr,_n)};E(Ot,Fr=>{n(oe).installed||Fr(ft)})}var qr=m(Ot,2),mr=d(qr),bn=d(mr),ma=m(on,2);{var ss=Fr=>{var _n=yh(),Jn=d(_n);N(()=>P(Jn,n(oe).loginStatus)),v(Fr,_n)};E(ma,Fr=>{n(oe).loginStatus&&Fr(ss)})}var os=m(ma,2),Pr=d(os);vs(Pr,{size:12,class:"text-amber-400 flex-shrink-0"}),N(()=>{P(Vr,n(oe).installed?"Codex CLI가 설치되었지만 로그인이 필요합니다":"Codex CLI 설치가 필요합니다"),P(bn,n(oe).installed?"1.":"2.")}),v(jr,Yn)};E(pr,jr=>{we()==="codex"&&jr(Ar)})}var Yr=m(pr,2),Mr=d(Yr);N(()=>P(Mr,n(oe).installed?"로그인 완료 후 새로고침하세요":"설치 완료 후 새로고침하세요")),v(zt,Zt)};E(ei,zt=>{n(_t)&&!xe().available&&zt(Sd)})}var ti=m(ei,2);{var Md=zt=>{var Zt=Sh(),pr=d(Zt),Ar=d(pr),Yr=d(Ar);_s(Yr,{size:13,class:"text-dl-success"});var Mr=m(Ar,2),jr=d(Mr);lv(jr,{size:11}),ae("click",Mr,Tt),v(zt,Zt)};E(ti,zt=>{we()==="codex"&&xe().available&&zt(Md)})}var Ed=m(ti,2);{var Ad=zt=>{var Zt=Lh(),pr=d(Zt),Ar=m(d(pr),2);{var Yr=Ot=>{vn(Ot,{size:12,class:"animate-spin text-dl-text-dim"})};E(Ar,Ot=>{n(Wt)&&Ot(Yr)})}var Mr=m(pr,2);{var jr=Ot=>{var ft=Mh(),qr=d(ft);vn(qr,{size:14,class:"animate-spin"}),v(Ot,ft)},Yn=Ot=>{var ft=Ah();Ie(ft,21,()=>n(Qt),Te,(qr,mr)=>{var bn=Eh(),ma=d(bn),ss=m(ma);{var os=Pr=>{ev(Pr,{size:10,class:"inline ml-1"})};E(ss,Pr=>{n(mr)===n(c)&&n(ht)&&Pr(os)})}N(Pr=>{Le(bn,1,Pr),P(ma,`${n(mr)??""} `)},[()=>Pt(Nt("px-3 py-1.5 rounded-lg text-[11px] border transition-all",n(mr)===n(c)&&n(ht)?"border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium":"border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"))]),ae("click",bn,()=>{we()!==n(l)&&gt(we()),fr(n(mr))}),v(qr,bn)}),v(Ot,ft)},Xn=Ot=>{var ft=zh();v(Ot,ft)};E(Mr,Ot=>{n(Wt)&&n(Qt).length===0?Ot(jr):n(Qt).length>0?Ot(Yn,1):Ot(Xn,-1)})}var Vr=m(Mr,2);{var on=Ot=>{var ft=$h(),qr=d(ft),mr=m(d(qr),2),bn=m(d(mr));Oi(bn,{size:9});var ma=m(qr,2);{var ss=Pr=>{var Fr=Th(),_n=d(Fr),Jn=d(_n),is=d(Jn);vn(is,{size:12,class:"animate-spin text-dl-primary-light"});var Zs=m(Jn,2),Ps=m(_n,2),$n=d(Ps),ln=m(Ps,2),eo=d(ln);N(()=>{Io($n,`width: ${n(x)??""}%`),P(eo,n($))}),ae("click",Zs,j),v(Pr,Fr)},os=Pr=>{var Fr=Nh(),_n=ee(Fr),Jn=d(_n),is=m(Jn,2),Zs=d(is);ws(Zs,{size:12});var Ps=m(_n,2);Ie(Ps,21,()=>nt,Te,($n,ln)=>{const eo=B(()=>n(Qt).some(Da=>Da===n(ln).name||Da===n(ln).name.split(":")[0]));var ri=ye(),zd=ee(ri);{var Td=Da=>{var to=Ph(),ni=d(to),ai=d(ni),si=d(ai),Id=d(si),oi=m(si,2),Pd=d(oi),Nd=m(oi,2);{var $d=ro=>{var li=Ih(),Vd=d(li);N(()=>P(Vd,n(ln).tag)),v(ro,li)};E(Nd,ro=>{n(ln).tag&&ro($d)})}var Ld=m(ai,2),Od=d(Ld),Rd=m(ni,2),ii=d(Rd),Dd=d(ii),jd=m(ii,2);ws(jd,{size:12,class:"text-dl-text-dim group-hover:text-dl-primary-light transition-colors"}),N(()=>{P(Id,n(ln).name),P(Pd,n(ln).size),P(Od,n(ln).desc),P(Dd,`${n(ln).gb??""} GB`)}),ae("click",to,()=>{u(q,n(ln).name,!0),w()}),v(Da,to)};E(zd,Da=>{n(eo)||Da(Td)})}v($n,ri)}),N($n=>is.disabled=$n,[()=>!n(q).trim()]),ae("keydown",Jn,$n=>{$n.key==="Enter"&&w()}),ja(Jn,()=>n(q),$n=>u(q,$n)),ae("click",is,w),v(Pr,Fr)};E(ma,Pr=>{n(le)?Pr(ss):Pr(os,-1)})}v(Ot,ft)};E(Vr,Ot=>{we()==="ollama"&&Ot(on)})}v(zt,Zt)};E(Ed,zt=>{(xe().available||n(dr)||n(_t))&&zt(Ad)})}v(Ft,Er)};E(bd,Ft=>{(n(kt)||n(ht))&&Ft(_d)})}N((Ft,Er)=>{Le(At,1,Ft),Le(Ir,1,Er),P(Qs,xe().label||we()),P(fd,xe().desc||"")},[()=>Pt(Nt("rounded-xl border transition-all",n(ht)?"border-dl-primary/40 bg-dl-primary/[0.03]":"border-dl-border")),()=>Pt(Nt("w-2.5 h-2.5 rounded-full flex-shrink-0",xe().available?"bg-dl-success":n(dr)?"bg-amber-400":"bg-dl-text-dim"))]),ae("click",Vt,()=>{xe().available||n(dr)?we()===n(l)?Dt(we()):gt(we()):Dt(we())}),v(R,At)});var xn=m(it,2),Nn=d(xn),Ee=d(Nn);{var ue=R=>{var V=ta();N(()=>{var ce;return P(V,`현재: ${(((ce=n(o)[n(l)])==null?void 0:ce.label)||n(l))??""} / ${n(c)??""}`)}),v(R,V)},lt=R=>{var V=ta();N(()=>{var ce;return P(V,`현재: ${(((ce=n(o)[n(l)])==null?void 0:ce.label)||n(l))??""}`)}),v(R,V)};E(Ee,R=>{n(l)&&n(c)?R(ue):n(l)&&R(lt,1)})}var Et=m(Nn,2);Aa(de,R=>u(te,R),()=>n(te)),ae("click",D,R=>{R.target===R.currentTarget&&u(y,!1)}),ae("click",$e,()=>u(y,!1)),ae("click",Et,()=>u(y,!1)),v(g,D)};E(Je,g=>{n(y)&&g(mt)})}var Lt=m(Je,2);{var Mt=g=>{var D=jh(),de=d(D),_e=m(d(de),4),Me=d(_e),$e=m(Me,2);Aa(de,st=>u(K,st),()=>n(K)),ae("click",D,st=>{st.target===st.currentTarget&&u(A,null)}),ae("click",Me,()=>u(A,null)),ae("click",$e,Ur),v(g,D)};E(Lt,g=>{n(A)&&g(Mt)})}var ir=m(Lt,2);{var Kr=g=>{const D=B(()=>T.recentCompanies||[]);var de=Uh(),_e=d(de),Me=d(_e),$e=d(Me);ys($e,{size:18,class:"text-dl-text-dim flex-shrink-0"});var st=m($e,2);Aa(st,R=>u(W,R),()=>n(W));var it=m(Me,2),Ut=d(it);{var xn=R=>{var V=qh(),ce=m(ee(V),2);Ie(ce,17,()=>n(Ae),Te,(we,xe,ht)=>{var kt=Vh(),dr=d(kt),_t=d(dr),Qt=m(dr,2),Wt=d(Qt),At=d(Wt),Vt=m(Wt,2),Ir=d(Vt),Oa=m(Qt,2),Ra=m(d(Oa),2);jn(Ra,{size:14,class:"text-dl-text-dim"}),N((Is,Qs)=>{Le(kt,1,Is),P(_t,Qs),P(At,n(xe).corpName),P(Ir,`${n(xe).stockCode??""} · ${(n(xe).market||"")??""}${n(xe).sector?` · ${n(xe).sector}`:""}`)},[()=>Pt(Nt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",ht===n(me)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(xe).corpName||"?").charAt(0)]),ae("click",kt,()=>{u(be,!1),u(ve,""),u(Ae,[],!0),u(me,-1),ze(n(xe))}),Va("mouseenter",kt,()=>{u(me,ht,!0)}),v(we,kt)}),v(R,V)},Nn=R=>{var V=Bh(),ce=m(ee(V),2);Ie(ce,17,()=>n(D),Te,(we,xe,ht)=>{var kt=Fh(),dr=d(kt),_t=d(dr),Qt=m(dr,2),Wt=d(Qt),At=d(Wt),Vt=m(Wt,2),Ir=d(Vt);N((Oa,Ra)=>{Le(kt,1,Oa),P(_t,Ra),P(At,n(xe).corpName),P(Ir,`${n(xe).stockCode??""} · ${(n(xe).market||"")??""}`)},[()=>Pt(Nt("flex items-center gap-3 w-full px-5 py-3 text-left transition-colors",ht===n(me)?"bg-dl-primary/10":"hover:bg-white/[0.03]")),()=>(n(xe).corpName||"?").charAt(0)]),ae("click",kt,()=>{u(be,!1),u(ve,""),u(me,-1),ze(n(xe))}),Va("mouseenter",kt,()=>{u(me,ht,!0)}),v(we,kt)}),v(R,V)},Ee=B(()=>n(ve).trim().length===0&&n(D).length>0),ue=R=>{var V=Gh();v(R,V)},lt=B(()=>n(ve).trim().length>0),Et=R=>{var V=Hh(),ce=d(V);ys(ce,{size:24,class:"mb-2 opacity-40"}),v(R,V)};E(Ut,R=>{n(Ae).length>0?R(xn):n(Ee)?R(Nn,1):n(lt)?R(ue,2):R(Et,-1)})}ae("click",de,R=>{R.target===R.currentTarget&&u(be,!1)}),ae("input",st,()=>{he&&clearTimeout(he),n(ve).trim().length>=1?he=setTimeout(async()=>{var R;try{const V=await Bl(n(ve).trim());u(Ae,((R=V.results)==null?void 0:R.slice(0,8))||[],!0)}catch{u(Ae,[],!0)}},250):u(Ae,[],!0)}),ae("keydown",st,R=>{const V=n(Ae).length>0?n(Ae):n(D);if(R.key==="ArrowDown")R.preventDefault(),u(me,Math.min(n(me)+1,V.length-1),!0);else if(R.key==="ArrowUp")R.preventDefault(),u(me,Math.max(n(me)-1,-1),!0);else if(R.key==="Enter"&&n(me)>=0&&V[n(me)]){R.preventDefault();const ce=V[n(me)];u(be,!1),u(ve,""),u(Ae,[],!0),u(me,-1),ze(ce)}else R.key==="Escape"&&u(be,!1)}),ja(st,()=>n(ve),R=>u(ve,R)),v(g,de)};E(ir,g=>{n(be)&&g(Kr)})}var lr=m(ir,2);{var Tr=g=>{var D=Wh(),de=d(D),_e=d(de),Me=d(_e),$e=m(_e,2),st=d($e);Bs(st,{size:14}),N(it=>{Le(de,1,it),P(Me,n(re))},[()=>Pt(Nt("surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",n(Y)==="error"?"bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light":n(Y)==="success"?"bg-dl-success/10 border-dl-success/30 text-dl-success":"bg-dl-bg-card border-dl-border text-dl-text"))]),ae("click",$e,()=>{u(X,!1)}),v(g,D)};E(lr,g=>{n(X)&&g(Tr)})}N(g=>{Le(Gt,1,Pt(n(tt)?n(p)?"sidebar-mobile":"hidden":"")),Le(rr,1,g)},[()=>Pt(Nt("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",n(_)?"text-dl-text-dim":n(ut)?"text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15":"text-dl-text-dim hover:text-dl-text-muted hover:bg-white/5"))]),ae("click",Gn,O),ae("click",Pn,Ke),ae("click",rr,()=>Re()),v(e,xt),nn()}Bn(["click","keydown","input"]);mu(Yh,{target:document.getElementById("app")});
