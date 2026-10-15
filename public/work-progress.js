// Each task contributes one equal share; its subtasks split that share.
export function taskFraction(task){
  if(task?.done)return 1;
  const subtasks=Array.isArray(task?.subtasks)?task.subtasks.filter(s=>s&&typeof s==='object'):[];
  return subtasks.length?subtasks.filter(s=>s.done).length/subtasks.length:0;
}
export function progressPercent(tasks){
  if(!Array.isArray(tasks)||!tasks.length)return 0;
  const value=tasks.reduce((sum,task)=>sum+taskFraction(task),0)/tasks.length;
  return value>=1-Number.EPSILON?100:Math.min(99,Math.round(value*100));
}
